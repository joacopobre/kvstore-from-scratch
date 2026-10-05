import os 

# fsync on the temp file makes the contents durable.
# rename makes the swap atomic, so no partial file is ever visible at the real path.
# fsync on the directory makes the rename durable.

def flush_memtable(memtable : dict, path:str) -> None :
    sorted_memtable = sorted(memtable.keys())
    temp_path = path + '.tmp'
    with open(temp_path,'wb') as f:
        for key in sorted_memtable:
            key_length = len(key).to_bytes(4, 'big')
            value = memtable.get(key)
            data_length = len(key) + len(value) + 4
            outer_length = data_length.to_bytes(4, 'big')
            f.write(outer_length + key_length + key + value)
        f.flush()
        os.fsync(f.fileno())
    os.rename(temp_path, path)
    dir_path = os.path.dirname(path) if os.path.dirname(path) != '' else "."
    dir_fd = os.open(dir_path, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
     


def read_sstable_linear(path) -> dict: 
    memtable = {}
    with open(path, 'rb') as f:
        while True:
            data_len = f.read(4)
            if(data_len == b''):
                break 
            data_len_int = int.from_bytes(data_len, 'big')
            data = f.read(data_len_int)
            
            key_len = int.from_bytes(data[0:4], 'big')
            key = data[4:4 + key_len]
            value = data[4 + key_len:]
            memtable[key] = value
            
    return memtable



