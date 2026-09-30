import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import flush_memtable, read_sstable_linear

memtable = {b"x": b"1", b"y": b"2", b"z": b"3"}
flush_memtable(memtable, 'sstable_test.bin')

result = read_sstable_linear('sstable_test.bin')
print(result)
assert result == memtable, "SSTable round-trip FAILED"
print("SSTable round-trip PASSED")