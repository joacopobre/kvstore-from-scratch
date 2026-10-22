from records import OP_DELETE, OP_SET, encode_record, decode_record
from utils.decode_entry import decode_sstable_entry
from utils.encode_entry import encode_sstable_entry


# --- record round-trips (from test.py) ---

def test_set_record_round_trip():
    record = encode_record(0, b"x", b"5")
    result = decode_record(record)
    assert result == (0, b"x", b"5"), "SET round-trip FAILED"


def test_delete_record_round_trip():
    record = encode_record(1, b"y")
    result = decode_record(record)
    assert result == (1, b"y", b""), "DELETE round-trip FAILED"


# --- encode_sstable_entry (from encode_test.py) ---

def test_encode_set_entry():
    result = encode_sstable_entry(OP_SET, b"x", b"1")

    outer = b"\x00\x00\x00\x07"   # inner part is 7 bytes
    flag = b"\x00"                # this is the OP_SET value in hex. Make sure it matches OP_SET
    key_length = b"\x00\x00\x00\x01"   # b"x" is 1 byte
    expected = outer + flag + key_length + b"x" + b"1"

    assert result == expected, 'failed'


def test_encode_tombstone_entry():
    result = encode_sstable_entry(OP_DELETE, b"x")   # no value argument

    outer = b"\x00\x00\x00\x06"   # inner part is 6 bytes
    flag = b"\x01"                # this is the OP_DELETE value in hex. Make sure it matches OP_DELETE
    key_length = b"\x00\x00\x00\x01"   # b"x" is 1 byte
    expected = outer + flag + key_length + b"x"

    assert result == expected, 'failed'


def test_encode_set_entry_empty_value():
    result = encode_sstable_entry(OP_SET, b"abc", b"")

    outer = b"\x00\x00\x00\x08"
    flag = b"\x00"
    key_length = b"\x00\x00\x00\x03"
    expected = outer + flag + key_length + b"abc"

    assert result == expected, 'failed'


# --- decode_sstable_entry (from decode_entry.py) ---

def test_decode_set_entry():
    flag       = b"\x00"              # OP_SET is 0
    key_length = b"\x00\x00\x00\x01"  # the key is 1 byte long
    data = flag + key_length + b"x" + b"1"

    result = decode_sstable_entry(data)

    assert result == (OP_SET, b"x", b"1")


def test_decode_tombstone_entry():
    flag       = b"\x01"
    key_length = b"\x00\x00\x00\x01"
    data = flag + key_length + b"x" + b""

    result = decode_sstable_entry(data)

    assert result == (OP_DELETE, b"x", b"")


def test_decode_set_entry_empty_value():
    flag       = b"\x00"
    key_length = b"\x00\x00\x00\x03"
    data = flag + key_length + b"abc" + b""

    result = decode_sstable_entry(data)

    assert result == (OP_SET, b"abc", b"")
