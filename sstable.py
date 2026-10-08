
import os
from utils.decode_entry import decode_sstable_entry
from utils.encode_entry import encode_sstable_entry



# fsync on the temp file makes the contents durable.
# rename makes the swap atomic, so no partial file is ever visible at the real path.
# fsync on the directory makes the rename durable.

def flush_memtable(memtable : dict, path:str) -> None :
    sorted_memtable = sorted(memtable.keys())
    temp_path = path + '.tmp'
    with open(temp_path,'wb') as f:
        for key in sorted_memtable:
            value = memtable.get(key)
            
            f.write(encode_sstable_entry(key, value))
        f.flush()
        os.fsync(f.fileno())
    os.rename(temp_path, path)
    dir_path = os.path.dirname(path) if os.path.dirname(path) != '' else "."
    dir_fd = os.open(dir_path, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def read_sstable_linear(path:str) -> dict: 
    memtable = {}
    with open(path, 'rb') as f:
        while True:
            data_len = f.read(4)
            if(data_len == b''):
                break 
            data_len_int = int.from_bytes(data_len, 'big')
            data = f.read(data_len_int)
            (key, value) = decode_sstable_entry(data)
            memtable[key] = value
            
    return memtable

def build_index(path:str) -> dict:
    index = {}
    with open(path, 'rb') as f:
        while True:
            start_offset = f.tell()
            data_len = f.read(4)
            if(data_len == b''):
                break 
            data_len_int = int.from_bytes(data_len, 'big')
            data = f.read(data_len_int)
            (key, _) = decode_sstable_entry(data)
            index[key] = start_offset
    return index

def get_from_sstable(path: str, index: dict, key: bytes )-> bytes | None:
    if key not in index: 
        return None 
    with open(path, 'rb') as f:
        f.seek(index[key])
        data_len = f.read(4)
        if data_len == b'':
            return None 
        data_len_int = int.from_bytes(data_len, 'big')
        data = f.read(data_len_int)
        (_, value) = decode_sstable_entry(data)
    return value 



