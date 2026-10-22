import os

from engine import Store
from sstable import get_all_sstables


# --- basic set/delete/recovery (from store_test.py) ---

def build_store(directory):
    s = Store(directory)   # Store instance

    # set some values
    s.set(b'x', b'1')
    s.set(b'y', b'2')
    s.set(b'z', b'3')

    # delete a value
    s.delete(b'y')
    return s


def test_set_round_trip(tmp_path):
    s = build_store(str(tmp_path))
    record = s.get(b'x')
    assert record == b'1', 'SET round-trip FAILD'


def test_delete_round_trip(tmp_path):
    s = build_store(str(tmp_path))
    record = s.get(b'y')   # should return None thus not printing
    assert record == None, 'DELETE round-trip FAILED'


def test_recovery_after_restart(tmp_path):
    directory = str(tmp_path)
    build_store(directory)

    s2 = Store(directory)  # a fresh instance — simulates a restart

    record = s2.get(b'x')
    assert record == b'1', 'Recovery FAILED for x'

    record = s2.get(b'y')
    assert record == None, 'Recovery FAILED — y should be deleted'

    record = s2.get(b'z')
    assert record == b'3', 'Recovery FAILED for z'


# --- flush (from check_flush.py) ---

def flush_round_1(directory):
    store = Store(directory)

    store.set(b"a", b"1")
    store.set(b"b", b"2")
    store.delete(b"b")
    store.flush()
    return store


def test_flush_round_1(tmp_path):
    directory = str(tmp_path)
    store = flush_round_1(directory)

    assert "sstable_000001.bin" in os.listdir(directory)
    assert len(store.sstable_list) == 1
    # the memtable is empty
    assert not store.memtable
    assert store.seq_num == 1


def test_flush_round_2(tmp_path):
    directory = str(tmp_path)
    store = flush_round_1(directory)

    store.set(b"c", b"3")
    store.flush()

    assert "sstable_000001.bin" in os.listdir(directory) and 'sstable_000002.bin' in os.listdir(directory)
    assert len(store.sstable_list) == 2 and store.seq_num == 2


def test_flush_empty_memtable(tmp_path):
    directory = str(tmp_path)
    store = Store(directory)
    store.flush()   # nothing was ever set

    # no sstable file exists, sstable_list is empty, seq_num is 0
    assert not os.listdir(directory)
    assert not store.sstable_list
    assert store.seq_num == 0


# --- WAL deleted on flush (from flush_wall_deleted.py) ---

def test_wal_removed_after_flush(tmp_path):
    directory = str(tmp_path)
    store = Store(directory)
    store.set(b"a", b"1")
    store.flush()

    # the WAL file no longer exists
    assert os.path.exists(os.path.join(directory, "wal.log")) == False


def test_data_survives_restart_through_sstable(tmp_path):
    directory = str(tmp_path)
    store = Store(directory)
    store.set(b"a", b"1")
    store.flush()

    restarted = Store(directory)
    assert restarted.get(b"a") == b"1"


def test_write_after_flush_then_restart(tmp_path):
    directory = str(tmp_path)
    store = Store(directory)
    store.set(b"a", b"1")
    store.flush()
    store.set(b"b", b"2")      # not flushed

    restarted = Store(directory)
    # both b"a" and b"b" are found, with the right values
    assert store.get(b'b')
    assert store.get(b'a')


def test_flush_on_empty_memtable_leaves_no_wal(tmp_path):
    directory = str(tmp_path)
    store = Store(directory)
    store.flush()
    # no sstable file exists and the call didn't crash
    assert os.path.exists(os.path.join(directory, "wal.log")) == False


# --- memtable_bytes accounting (from memtable_bytes_test.py) ---

EXPECTED_MEMTABLE_BYTES = (len(b'x') + len(b'hello')) \
     + (len(b'a') + len(b'hellou')) \
     + (len(b'a') + 1)


def build_counted_store(directory):
    s = Store(directory)

    s.set(b'x', b'hello')
    s.set(b'a', b'hellou')
    s.delete(b'a')
    return s


def test_memtable_bytes_counts_writes(tmp_path):
    s = build_counted_store(str(tmp_path))
    assert s.memtable_bytes == EXPECTED_MEMTABLE_BYTES


def test_memtable_bytes_rebuilt_on_restart(tmp_path):
    directory = str(tmp_path)
    build_counted_store(directory)

    s2 = Store(directory)
    assert s2.memtable_bytes == EXPECTED_MEMTABLE_BYTES


def test_memtable_bytes_zero_after_flush(tmp_path):
    directory = str(tmp_path)
    build_counted_store(directory)

    s2 = Store(directory)
    s2.flush()
    assert s2.memtable_bytes == 0


def test_memtable_bytes_after_flush_counts_new_write(tmp_path):
    directory = str(tmp_path)
    build_counted_store(directory)

    s2 = Store(directory)
    s2.flush()
    s2.set(b'k', b'vv')
    assert s2.memtable_bytes == len(b'k') + len(b'vv')


# --- recovery across SSTables (from sstable_recovery_test.py) ---

def test_sstable_recovery(tmp_path):
    directory = str(tmp_path)
    s = Store(directory)

    s.set(b'x', b'1')
    s.set(b'y', b'2')
    s.set(b'z', b'3')

    s.delete(b'y')
    s.flush()

    s.set(b'x', b'4')
    s.flush()

    s2 = Store(directory)
    assert s2.get(b'x') == b'4'
    assert s2.get(b'z') == b'3'
    assert s2.get(b'y') == None

    assert len(s2.sstable_list) == 2
    assert s2.seq_num == 2


# --- automatic flush at the memtable limit (from maybe_flush_test.py) ---

def test_boundary(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=10)

    # one write that brings memtable_bytes to 9
    # (hand-compute: len(key) + len(value))
    s.set(b'a', b'asdfghas')
    assert s.memtable_bytes == 9
    assert len(get_all_sstables(directory)) == 0

    # one more write that brings the total to exactly 10
    # (it is the total that counts, not the single write)
    s.set(b's', b'asd')
    assert len(get_all_sstables(directory)) == 1
    assert s.memtable_bytes == 0
    assert not s.memtable


def test_oversized_single_write(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=10)

    # one set whose key + value is clearly more than 10
    s.set(b'sdfasdf', b'asdfsafqwewd')
    assert len(get_all_sstables(directory)) == 1
    assert s.memtable_bytes == 0
    # get(...) still returns that value (now served from the SSTable)
    assert s.get(b'sdfasdf') == b'asdfsafqwewd'


def test_writes_after_auto_flush(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=10)

    # writes that cross the limit, remembering one key from before the flush
    s.set(b'saassdf', b'holaquetal')
    assert len(get_all_sstables(directory)) == 1

    # get(old_key) returns its value (from the SSTable)
    assert s.get(b'saassdf') == b'holaquetal'
    # a small new write that does NOT cross the limit
    s.set(b'g', b'hi')
    # get(new_key) returns its value (from the memtable)
    assert s.get(b'g') == b'hi'
    # memtable_bytes == the size of just that new write
    assert s.memtable_bytes == 3
    assert len(get_all_sstables(directory)) == 1  # no second flush


# --- WAL over the limit at startup (from test_wal_over_limit_at_startup.py) ---

def test_restart_then_cross_limit(tmp_path):
    directory = str(tmp_path)
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


def test_wal_over_limit_at_startup(tmp_path):
    directory = str(tmp_path)
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
