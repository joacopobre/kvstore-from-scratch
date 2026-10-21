
import os
from utils.decode_entry import decode_sstable_entry
from utils.encode_entry import encode_sstable_entry
from records import TOMBSTONE, OP_DELETE, OP_SET

SEQ_WIDTH = 6
SEQ_PREFIX = 'sstable_'
SEQ_SUFFIX = '.bin'
PREFIX_LEN = len(SEQ_PREFIX)
SUFFIX_LEN = len(SEQ_SUFFIX)
# fsync on the temp file makes the contents durable.
# rename makes the swap atomic, so no partial file is ever visible at the real path.
# fsync on the directory makes the rename durable.

def flush_memtable(memtable : dict, path:str) -> None :
    sorted_memtable = sorted(memtable.keys())
    temp_path = path + '.tmp'
    with open(temp_path,'wb') as f:
        for key in sorted_memtable:
            value = memtable[key]
            if value is TOMBSTONE:
                f.write(encode_sstable_entry(OP_DELETE, key))
            else:
                f.write(encode_sstable_entry(OP_SET, key, value))
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
    entries = {}
    with open(path, 'rb') as f:
        while True:
            data_len = f.read(4)
            if(data_len == b''):
                break 
            data_len_int = int.from_bytes(data_len, 'big')
            data = f.read(data_len_int)
            (op_type, key, value) = decode_sstable_entry(data)
            if op_type == OP_DELETE:
                entries[key] = TOMBSTONE
            else:
                entries[key] = value
            
    return entries

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
            (_, key, _) = decode_sstable_entry(data)
            index[key] = start_offset
    return index

def get_from_sstable(path: str, index: dict, key: bytes )-> bytes | None | object:
    if key not in index: 
        return None 
    with open(path, 'rb') as f:
        f.seek(index[key])
        data_len = f.read(4)
        if data_len == b'':
            return None 
        data_len_int = int.from_bytes(data_len, 'big')
        data = f.read(data_len_int)
        (op_type, _, value) = decode_sstable_entry(data)
        # returns TOMBSTONE for a deleted key
        if op_type == OP_DELETE:
            return TOMBSTONE
    return value 

def generate_padded_filepath(directory: str, seq: int)-> str:
    name = SEQ_PREFIX + str(seq).zfill(SEQ_WIDTH) + SEQ_SUFFIX
    return os.path.join(directory, name)

def get_latest_seq(directory: str) -> int:
    files = os.listdir(directory)
    latest = 0
    
    for file in files:
        if file.startswith(SEQ_PREFIX) and file.endswith(SEQ_SUFFIX):
            number = file[PREFIX_LEN: -SUFFIX_LEN]
            if number.isdigit(): 
                latest = max(latest, int(number))

    return latest

def get_all_sstables(directory: str)-> list[str]:
    files = []
    directory_files = os.listdir(directory)
    for file in directory_files:
        if file.startswith(SEQ_PREFIX) and file.endswith(SEQ_SUFFIX):
                number = file[PREFIX_LEN: -SUFFIX_LEN]
                if number.isdigit(): 
                    files.append((int(number),os.path.join(directory, file)))
    paths = []
    for number, path in sorted(files):
        paths.append(path)
    return paths

def merge_tables(tables: list[dict], drop_tombstones: bool)-> dict:
    result = {}
    tombstones = {}

    for table in reversed(tables):
        for key, value in table.items():
            # if we are dropping TOMBSTONES
            if drop_tombstones:
                if value is TOMBSTONE and key not in tombstones:
                    tombstones[key] = value
                    continue
                elif key in tombstones:
                    continue
            if key not in result:
                result[key] = value

    return result 







