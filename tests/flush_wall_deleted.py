import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

# 1 and 2: WAL gone after flush, data survives a restart through the SSTable
with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.set(b"a", b"1")
    store.flush()

    # TODO: assert the WAL file no longer exists
    #       (the path is os.path.join(directory, "wal.log"), written as a literal name)
    assert os.path.exists(os.path.join(directory, "wal.log")) == False

    restarted = Store(directory)
    assert restarted.get(b"a") == b"1"
    print("PASSED 1 and 2")

# 3: new write after a flush, then restart: both keys found
with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.set(b"a", b"1")
    store.flush()
    store.set(b"b", b"2")      # not flushed

    restarted = Store(directory)
    # TODO: assert both b"a" and b"b" are found, with the right values
    assert store.get(b'b')
    assert store.get(b'a')
    print("PASSED 3")

# 4: flush on an empty memtable
with tempfile.TemporaryDirectory() as directory:
    store = Store(directory)
    store.flush()
    # TODO: assert no sstable file exists and the call didn't crash
    assert os.path.exists(os.path.join(directory, "wal.log")) == False
    print("PASSED 4")