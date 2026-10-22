import os

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


# --- explicit compaction (from compact_test.py) ---

def test_compact_three_files(tmp_path):
    directory = str(tmp_path)
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


def test_compact_survives_restart(tmp_path):
    directory = str(tmp_path)
    s = build_three_files(directory)
    s.compact()

    s2 = Store(directory)

    assert s2.get(b'a') is None
    assert s2.get(b'b') == b'3'

    assert len(s2.sstable_list) == 1


def test_write_after_compact(tmp_path):
    directory = str(tmp_path)
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


def test_compact_small_cases(tmp_path):
    directory = str(tmp_path)
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


def write_merged_file_4(directory):
    path = generate_padded_filepath(directory, 4)
    flush_memtable({b'b': b'3'}, path)


def assert_correct_answers(directory):
    s = Store(directory)               # a NEW store each time: rebuilt from disk only
    assert s.get(b'a') is None
    assert s.get(b'b') == b'3'


def test_partial_compaction_delete_order(tmp_path):
    directory = str(tmp_path)
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


def test_partial_compaction_wrong_delete_order(tmp_path):
    directory = str(tmp_path)
    build_three_files(directory)
    write_merged_file_4(directory)

    # State C: the WRONG order. File 3 (the tombstone) is deleted first
    files = get_all_sstables(directory)
    os.remove(files[2])
    s2 = Store(directory)
    assert s2.get(b'a') == b'1'             # the deleted key came back: the bug


def test_partial_compaction_leftover_tmp_file(tmp_path):
    directory = str(tmp_path)
    build_three_files(directory)

    # State D: crash BEFORE the rename: only a leftover .tmp file exists
    tmp_file_path = generate_padded_filepath(directory, 4) + '.tmp'
    with open(tmp_file_path, 'wb') as f:
        f.write(b'junk')
    assert len(get_all_sstables(directory)) == 3     # the .tmp is ignored
    assert_correct_answers(directory)


def test_compact_all_keys_deleted(tmp_path):
    directory = str(tmp_path)
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


def test_compact_leaves_memtable_alone(tmp_path):
    directory = str(tmp_path)
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


# --- automatic compaction at the threshold (from compaction_trigger_test.py) ---

def count_files(directory):
    return len(get_all_sstables(directory))


def test_compaction_triggers_at_threshold(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=4, compaction_threshold=3)

    s.set(b'ccc', b'1')          # 4 bytes -> flush -> file 1
    assert count_files(directory) == 1
    s.set(b'a', b'111')          # 4 bytes -> flush -> file 2
    assert count_files(directory) == 2
    s.delete(b'ccc')             # 4 bytes -> flush -> file 3 -> compaction runs
    assert count_files(directory) == 1

    assert get_latest_seq(directory) == 4
    assert s.seq_num == 4
    assert len(s.sstable_list) == 1
    assert s.get(b'ccc') is None
    assert s.get(b'a') == b'111'
    # the tombstone and the stale value are physically gone
    assert read_sstable_linear(get_all_sstables(directory)[0]) == {b'a': b'111'}

    # writes keep working after an automatic compaction
    s.set(b'b', b'777')          # 4 bytes -> flush -> file 5 (2 files, below threshold)
    assert count_files(directory) == 2
    assert get_latest_seq(directory) == 5
    assert s.get(b'b') == b'777'
    assert s.get(b'a') == b'111'
    assert s.get(b'ccc') is None


def test_no_compaction_below_threshold(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=4, compaction_threshold=4)

    s.set(b'ccc', b'1')
    s.set(b'a', b'111')
    s.delete(b'ccc')

    assert count_files(directory) == 3       # 3 files < 4, nothing merged
    assert s.get(b'ccc') is None             # the tombstone is still doing its job
    assert s.get(b'a') == b'111'


def test_compaction_threshold_counts_files_after_restart(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=4, compaction_threshold=3)
    s.set(b'ccc', b'1')          # file 1
    s.set(b'a', b'111')          # file 2
    assert count_files(directory) == 2

    s2 = Store(directory, memtable_limit=4, compaction_threshold=3)
    assert len(s2.sstable_list) == 2         # rebuilt from the directory
    s2.set(b'z', b'999')         # 4 bytes -> flush -> 3 files -> compaction
    assert count_files(directory) == 1
    assert s2.get(b'ccc') == b'1'
    assert s2.get(b'a') == b'111'
    assert s2.get(b'z') == b'999'
