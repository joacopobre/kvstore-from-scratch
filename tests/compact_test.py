import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store
from sstable import get_all_sstables, get_latest_seq, read_sstable_linear, generate_padded_filepath, flush_memtable


def build_three_files(directory):
    s = Store(directory)
    s.set(b'a', b'1')
    s.set(b'b', b'2')
    s.flush()            # file 1: a=1, b=2
    s.set(b'b', b'3')
    s.flush()            # file 2: b=3
    s.delete(b'a')
    s.flush()            # file 3: a=TOMBSTONE
    return s


def test_compact_three_files():
    with tempfile.TemporaryDirectory() as directory:
        s = build_three_files(directory)
        assert len(get_all_sstables(directory)) == 3

        s.compact()     

        files = get_all_sstables(directory)
        assert len(files) == 1
        
        assert get_latest_seq(directory) == 4 
        assert s.seq_num == 4
        
        assert len(s.sstable_list) == 1
        assert s.get(b'a') is None
        assert s.get(b'b') == b'3'

        # the tombstone and the stale values are physically gone from disk
        
        on_disk = read_sstable_linear(files[0])
        assert on_disk == {b'b': b'3'}


def test_compact_survives_restart():
    with tempfile.TemporaryDirectory() as directory:
        s = build_three_files(directory)
        s.compact()

        s2 = Store(directory)
        
        assert s2.get(b'a') is None
        assert s2.get(b'b') == b'3'
        
        assert len(s2.sstable_list) == 1


def test_write_after_compact():
    with tempfile.TemporaryDirectory() as directory:
        s = build_three_files(directory)
        s.compact()

        s.set(b'c', b'9')
        s.flush()
        
        files = get_all_sstables(directory)
        assert len(files) == 2
        assert get_latest_seq(directory) == 5
        assert s.seq_num == 5
        
       
        assert s.get(b'c') == b'9'
        assert s.get(b'b') == b'3'
        assert s.get(b'a') is None


def test_compact_small_cases():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory)
        s.compact()
        

        assert get_all_sstables(directory) == []
        s.compact()
        assert get_all_sstables(directory) == []
        assert s.sstable_list == []
        assert s.seq_num == 0
        s.set(b'x', b'1')
        s.flush()
        before = get_all_sstables(directory)    # captured before compaction
        s.compact()
        after = get_all_sstables(directory)
        assert before == after
        assert len(s.sstable_list) == 1
        assert s.get(b'x') == b'1'


test_compact_three_files()
test_compact_survives_restart()
test_write_after_compact()
test_compact_small_cases()


def write_merged_file_4(directory):
    path = generate_padded_filepath(directory, 4)
    flush_memtable({b'b': b'3'}, path)


def assert_correct_answers(directory):
    s = Store(directory)               # a NEW store each time: rebuilt from disk only
    assert s.get(b'a') is None
    assert s.get(b'b') == b'3'


def test_partial_compaction_states():
    with tempfile.TemporaryDirectory() as directory:
        build_three_files(directory)
        write_merged_file_4(directory)

        # State A: files 1, 2, 3, 4 (crash right after the rename)
        assert len(get_all_sstables(directory)) == 4
        assert_correct_answers(directory)

        files = get_all_sstables(directory)     # oldest first: [1, 2, 3, 4]

        # State B1: oldest-first delete, file 1 gone
        os.remove(files[0])
        assert_correct_answers(directory)

        # State B2: files 3 and 4 left
        os.remove(files[1])
        assert_correct_answers(directory)

        # State B3: only file 4 left (compaction finished)
        os.remove(files[2])
        assert len(get_all_sstables(directory)) == 1
        assert_correct_answers(directory)

    with tempfile.TemporaryDirectory() as directory:
        build_three_files(directory)
        write_merged_file_4(directory)

        # State C: the WRONG order. File 3 (the tombstone) is deleted first
        files = get_all_sstables(directory)
        os.remove(files[2])
        s2 = Store(directory)
        assert s2.get(b'a') == b'1'             # the deleted key came back: the bug

    with tempfile.TemporaryDirectory() as directory:
        build_three_files(directory)

        # State D: crash BEFORE the rename: only a leftover .tmp file exists
        tmp_path = generate_padded_filepath(directory, 4) + '.tmp'
        with open(tmp_path, 'wb') as f:
            f.write(b'junk')
        assert len(get_all_sstables(directory)) == 3     # the .tmp is ignored
        assert_correct_answers(directory)


def test_compact_all_keys_deleted():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory)
        s.set(b'a', b'1')
        s.flush()
        s.delete(b'a')
        s.flush()

        s.compact()
        assert s.get(b'a') is None
        # current behaviour: the merged dict is empty, so one empty SSTable is written
        assert len(get_all_sstables(directory)) == 1
        assert len(s.sstable_list) == 1

        s2 = Store(directory)                   # a restart must open fine too
        assert s2.get(b'a') is None


def test_compact_leaves_memtable_alone():
    with tempfile.TemporaryDirectory() as directory:
        s = build_three_files(directory)
        s.set(b'z', b'9')                       # in the memtable and the WAL, not flushed
        before = s.memtable_bytes

        s.compact()
        assert s.get(b'z') == b'9'
        assert s.memtable == {b'z': b'9'}
        assert s.memtable_bytes == before

        s2 = Store(directory)                   # WAL replay must still bring z back
        assert s2.get(b'z') == b'9'
        assert s2.get(b'b') == b'3'
        assert s2.get(b'a') is None


test_partial_compaction_states()
test_compact_all_keys_deleted()
test_compact_leaves_memtable_alone()