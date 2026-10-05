import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import read_sstable_linear

result = read_sstable_linear('sstable_test.bin')
print(result)

assert result == {b"old": b"1"} , 'SSTable does not returs last good state'
print("'SSTable returs last good state'")

assert os.path.exists('sstable_test.bin.tmp') == True, 'temp file does not exists'
print("temp file exists")

tmp_result = read_sstable_linear('sstable_test.bin.tmp')
assert tmp_result == {b"new": b"2"}