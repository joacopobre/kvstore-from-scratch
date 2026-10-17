import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)

    # round 1
    store.set(b"a", b"1")
    store.set(b"b", b"2")
    store.delete(b"b")
    store.flush()

    # TODO: assert "sstable_000001.bin" is in os.listdir(directory)
    assert "sstable_000001.bin" in os.listdir(directory)
    # TODO: assert len(store.sstable_list) == 1
    assert len(store.sstable_list) == 1
    # TODO: assert the memtable is empty
    assert not store.memtable
    # TODO: assert store.seq_num == 1
    assert store.seq_num == 1 
    print("PASSED round 1")

    # round 2
    store.set(b"c", b"3")
    store.flush()

    # TODO: assert both sstable_000001.bin AND sstable_000002.bin are in the directory
    assert "sstable_000001.bin" in os.listdir(directory) and 'sstable_000002.bin' in os.listdir(directory)
    # TODO: assert len(store.sstable_list) == 2 and store.seq_num == 2
    assert len(store.sstable_list) == 2 and store.seq_num == 2
    print("PASSED round 2")

with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.flush()   # nothing was ever set

    # TODO: assert no sstable file exists, sstable_list is empty, seq_num is 0
    assert not os.listdir(directory)
    assert not store.sstable_list 
    assert store.seq_num == 0
    print("PASSED empty flush")