import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store
from sstable import get_all_sstables


def test_restart_then_cross_limit():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=20)

        s.set(b'aa', b'bbb')   # 2 + 3 = 5
        s.set(b'cc', b'dd')    # 2 + 2 = 4
        s.set(b'e', b'ff')     # 1 + 2 = 3   -> total 12
        assert s.memtable_bytes == 12
        assert len(get_all_sstables(directory)) == 0

        s2 = Store(directory, memtable_limit=20)
        assert s2.memtable_bytes == 12          # replay rebuilt the counter
        assert len(get_all_sstables(directory)) == 0

        s2.set(b'gg', b'hhhh') # 2 + 4 = 6     -> total 18, under the limit
        assert s2.memtable_bytes == 18
        assert len(get_all_sstables(directory)) == 0

        s2.set(b'i', b'j')     # 1 + 1 = 2     -> total 20, hits the limit
        assert len(get_all_sstables(directory)) == 1
        assert s2.memtable_bytes == 0
        assert not s2.memtable

        assert s2.get(b'aa') == b'bbb'          # written before the restart
        assert s2.get(b'i') == b'j'             # written after the restart


def test_wal_over_limit_at_startup():
    with tempfile.TemporaryDirectory() as directory:
        s = Store(directory, memtable_limit=1000)

        s.set(b'key1', b'value1')   # 4 + 6 = 10
        s.set(b'key2', b'value2')   # 10
        s.set(b'key3', b'value3')   # 10  -> total 30
        assert s.memtable_bytes == 30
        assert len(get_all_sstables(directory)) == 0

        s2 = Store(directory, memtable_limit=20)   # same data, smaller limit

        # Option 1: __init__ ends with a flush, so the store opens already under the limit
        assert len(get_all_sstables(directory)) == 1
        assert s2.memtable_bytes == 0
        assert not s2.memtable

        assert s2.get(b'key1') == b'value1'
        assert s2.get(b'key2') == b'value2'
        assert s2.get(b'key3') == b'value3'


test_restart_then_cross_limit()
test_wal_over_limit_at_startup()