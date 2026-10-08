import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import flush_memtable, build_index, get_from_sstable

memtable = {b"x": b"1", b"y": b"2", b"z": b"3"}
flush_memtable(memtable, 'test_memtable.bin')

index = build_index('test_memtable.bin')
assert index == {b"x": 0, b"y": 10, b"z": 20}, "FAILED"
print("PASS" , index)

result = get_from_sstable('test_memtable.bin', index, b'z')
assert result == b'3', "FAILED"
print('PASS', result) 

result = get_from_sstable('test_memtable.bin', index, b'y')
assert result == b'2', "FAILED"
print('PASS', result)

result = get_from_sstable('test_memtable.bin', index, b'x')
assert result == b'1', "FAILED"
print('PASS', result)

result = get_from_sstable('test_memtable.bin', index, b'q')
assert result == None, "FAILED"
print('PASS', result)


