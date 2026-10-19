import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store
from sstable import get_all_sstables


def test_boundary():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=10)

        # TODO: one write that brings memtable_bytes to 9
        # (hand-compute: len(key) + len(value))
        s.set(b'a',b'asdfghas')
        assert s.memtable_bytes == 9
        assert len(get_all_sstables(directory)) == 0

        # TODO: one more write that brings the total to exactly 10
        # (it is the total that counts, not the single write)
        s.set(b's',b'asd')
        assert len(get_all_sstables(directory)) == 1
        assert s.memtable_bytes == 0
        assert not s.memtable


def test_oversized_single_write():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=10)

        # TODO: one set whose key + value is clearly more than 10
        s.set(b'sdfasdf', b'asdfsafqwewd')
        assert len(get_all_sstables(directory)) == 1
        assert s.memtable_bytes == 0
        # TODO: assert get(...) still returns that value (now served from the SSTable)
        assert s.get(b'sdfasdf') == b'asdfsafqwewd'


def test_writes_after_auto_flush():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=10)

        # TODO: writes that cross the limit, remembering one key from before the flush
        s.set(b'saassdf', b'holaquetal')
        assert len(get_all_sstables(directory)) == 1

        # TODO: assert get(old_key) returns its value (from the SSTable)
        assert s.get(b'saassdf') == b'holaquetal'
        # TODO: a small new write that does NOT cross the limit
        s.set(b'g',b'hi')
        # TODO: assert get(new_key) returns its value (from the memtable)
        assert s.get(b'g') == b'hi'
        # TODO: assert memtable_bytes == the size of just that new write
        assert s.memtable_bytes == 3 
        assert len(get_all_sstables(directory)) == 1  # no second flush


test_boundary()
test_oversized_single_write()
test_writes_after_auto_flush()