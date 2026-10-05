import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import flush_memtable

path = 'sstable_test.bin'
flush_memtable({b"old": b"1"}, path)  

new_memtable = {b"new": b"2"}

sorted_memtable = sorted(new_memtable.keys())
temp_path = path + '.tmp'
with open(temp_path,'wb') as f:
    for key in sorted_memtable:
        key_length = len(key).to_bytes(4, 'big')
        value = new_memtable.get(key)
        data_length = len(key) + len(value) + 4
        outer_length = data_length.to_bytes(4, 'big')
        f.write(outer_length + key_length + key + value)
    f.flush()
    os.fsync(f.fileno())
os._exit(1) #emulate crash
