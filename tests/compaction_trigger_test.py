import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store
from sstable import get_all_sstables, get_latest_seq, read_sstable_linear


def count_files(directory):
    return len(get_all_sstables(directory))


def test_compaction_triggers_at_threshold():
    with tempfile.TemporaryDirectory() as directory:
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


def test_no_compaction_below_threshold():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=4, compaction_threshold=4)

        s.set(b'ccc', b'1')
        s.set(b'a', b'111')
        s.delete(b'ccc')

        assert count_files(directory) == 3       # 3 files < 4, nothing merged
        assert s.get(b'ccc') is None             # the tombstone is still doing its job
        assert s.get(b'a') == b'111'


def test_compaction_threshold_counts_files_after_restart():
    with tempfile.TemporaryDirectory() as directory:
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


test_compaction_triggers_at_threshold()
test_no_compaction_below_threshold()
test_compaction_threshold_counts_files_after_restart()