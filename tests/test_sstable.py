import os

from records import TOMBSTONE
from sstable import (
    build_index,
    flush_memtable,
    generate_padded_filepath,
    get_all_sstables,
    get_from_sstable,
    get_latest_seq,
    merge_tables,
    read_sstable_linear,
)


# --- generate_padded_filepath (from generate_padded_filepath_check.py) ---

def test_generate_padded_filepath_pads_small_seq():
    result = generate_padded_filepath(directory='data', seq=2)
    expect = os.path.join("data", "sstable_000002.bin")
    assert result == expect


def test_generate_padded_filepath_long_seq():
    result = generate_padded_filepath(directory='data', seq=123456)
    expect = os.path.join("data", "sstable_123456.bin")
    assert result == expect


def test_generate_padded_filepath_single_digit_seq():
    result = generate_padded_filepath(directory='data', seq=7)
    expect = os.path.join("data", "sstable_000007.bin")
    assert result == expect


# --- get_all_sstables (from get_all_sstables_test.py) ---

def test_get_all_sstables_order_and_noise(tmp_path):
    directory = str(tmp_path)
    for name in ["sstable_000003.bin", "sstable_000001.bin", 'sstable_999999.bin', 'sstable_1000000.bin', "sstable_000002.bin", "wal.log"]:
        open(os.path.join(directory, name), "wb").close()

    result = get_all_sstables(directory)

    expected = [
        os.path.join(directory, "sstable_000001.bin"),
        os.path.join(directory, "sstable_000002.bin"),
        os.path.join(directory, "sstable_000003.bin"),
        os.path.join(directory, "sstable_999999.bin"),
        os.path.join(directory, "sstable_1000000.bin"),
    ]
    assert result == expected


# --- get_latest_seq (from latest_seq_test.py) ---

def test_get_latest_seq_no_sstables(tmp_path):
    directory = str(tmp_path)
    open(os.path.join(directory, "hello.txt"), "wb").close()   # makes an empty file
    result = get_latest_seq(directory)
    assert result == 0


def test_get_latest_seq_picks_highest(tmp_path):
    directory = str(tmp_path)
    open(os.path.join(directory, "sstable_000001.bin"), "wb").close()
    open(os.path.join(directory, "sstable_000030.bin"), "wb").close()
    open(os.path.join(directory, "sstable_000020.bin"), "wb").close()
    result = get_latest_seq(directory)
    assert result == 30


def test_get_latest_seq_ignores_tmp_files(tmp_path):
    directory = str(tmp_path)
    open(os.path.join(directory, "sstable_000001.bin"), "wb").close()
    open(os.path.join(directory, "sstable_000030.bin"), "wb").close()
    open(os.path.join(directory, "sstable_000005.bin.tmp"), "wb").close()
    result = get_latest_seq(directory)
    assert result == 30


# --- flush_memtable / read_sstable_linear round trip (from round_trip.py) ---

def test_flush_read_round_trip(tmp_path):
    memtable = {b"a": b"1", b"b": TOMBSTONE, b"c": b""}
    path = os.path.join(str(tmp_path), 'flushed_sstable.bin')
    flush_memtable(memtable, path)

    result = read_sstable_linear(path)

    assert result == memtable


# --- build_index / get_from_sstable (from test_index.py) ---

def build_indexed_sstable(tmp_path):
    memtable = {b"x": b"1", b"y": b"2", b"z": b"3"}
    path = os.path.join(str(tmp_path), 'test_memtable.bin')
    flush_memtable(memtable, path)
    return path, build_index(path)


def test_build_index_offsets(tmp_path):
    path, index = build_indexed_sstable(tmp_path)
    assert index == {b"x": 0, b"y": 11, b"z": 22}, "FAILED"


def test_get_from_sstable_last_key(tmp_path):
    path, index = build_indexed_sstable(tmp_path)
    result = get_from_sstable(path, index, b'z')
    assert result == b'3', "FAILED"


def test_get_from_sstable_middle_key(tmp_path):
    path, index = build_indexed_sstable(tmp_path)
    result = get_from_sstable(path, index, b'y')
    assert result == b'2', "FAILED"


def test_get_from_sstable_first_key(tmp_path):
    path, index = build_indexed_sstable(tmp_path)
    result = get_from_sstable(path, index, b'x')
    assert result == b'1', "FAILED"


def test_get_from_sstable_missing_key_is_none(tmp_path):
    path, index = build_indexed_sstable(tmp_path)
    result = get_from_sstable(path, index, b'q')
    assert result == None, "FAILED"


# --- get_from_sstable with a tombstone (from get_from_sstable_test.py) ---

def build_sstable_with_tombstone(tmp_path):
    path = os.path.join(str(tmp_path), 'get_test.bin')
    flush_memtable({b"a": b"1", b"b": TOMBSTONE}, path)
    return path, build_index(path)


def test_get_from_sstable_returns_value(tmp_path):
    path, index = build_sstable_with_tombstone(tmp_path)
    # 1. a real value comes back as bytes
    assert get_from_sstable(path, index, b"a") == b"1"


def test_get_from_sstable_returns_tombstone(tmp_path):
    path, index = build_sstable_with_tombstone(tmp_path)
    # 2. lookup of b"b" should be TOMBSTONE (use `is`, not ==)
    assert get_from_sstable(path, index, b"b") is TOMBSTONE


def test_get_from_sstable_absent_key_is_none_not_tombstone(tmp_path):
    path, index = build_sstable_with_tombstone(tmp_path)
    # 3. lookup of b"z" (not in the file) should be None,
    #    and also assert it is NOT TOMBSTONE
    assert get_from_sstable(path, index, b"z") is None


def test_get_from_sstable_scrambled_order(tmp_path):
    path, index = build_sstable_with_tombstone(tmp_path)
    # 4. look the keys up in scrambled order (b, then a, then z)
    #    and check the three answers are the same as before
    assert get_from_sstable(path, index, b"b") is TOMBSTONE
    assert get_from_sstable(path, index, b"a") == b"1"
    assert get_from_sstable(path, index, b"z") is None


# --- merge_tables (from merge_tables_test.py) ---

def sample_tables():
    return [{b'a': b'1', b'b': b'2', b'c': b'3'}, {b'b': b'20', b'd': b'4'}, {b'a': TOMBSTONE, b'e': b'5'}]


def test_merge_tables_keeps_tombstone():
    result = merge_tables(sample_tables(), False)
    expected = {b'a': TOMBSTONE, b'b': b'20', b'c': b'3', b'd': b'4', b'e': b'5'}
    assert result == expected


def test_merge_tables_drops_tombstone():
    result = merge_tables(sample_tables(), True)
    expected = {b'b': b'20', b'c': b'3', b'd': b'4', b'e': b'5'}
    assert result == expected
