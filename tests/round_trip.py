
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from records import TOMBSTONE
from sstable import flush_memtable, read_sstable_linear

memtable = {b"a": b"1", b"b": TOMBSTONE, b"c": b""}
path = 'flushed_sstable.bin'
flush_memtable(memtable, path)

result = read_sstable_linear(path)

assert result == memtable 
print('PASS')