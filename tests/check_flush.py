import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from records import TOMBSTONE
from sstable import  flush_memtable

memtable = {b"a": b"1", b"b": TOMBSTONE}

flush_memtable(memtable, 'flush_tombstone_test.bin')

with open('flush_tombstone_test.bin', "rb") as f:
    actual = f.read()

row_a = b"\x00\x00\x00\x07" + b"\x00" + b"\x00\x00\x00\x01" + b"a" + b"1"
row_b = b"\x00\x00\x00\x06" + b"\x01" + b"\x00\x00\x00\x01" + b"b" + b""

expected = row_a + row_b

assert expected == actual 

print("PASSED")