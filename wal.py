import os 

def append_entry(path:str, data:bytes)->None:
    with open(path, 'ab') as f:
        length = len(data)
        len_prefix = length.to_bytes(4, 'big')
        f.write(len_prefix + data)
        f.flush()
        os.fsync(f.fileno())

def _scan_entries(path:str)-> tuple[list[bytes], int]:
    if not os.path.exists(path): return [], 0
    last_good_ofset = 0
    entries = []
    with open(path, 'rb')as f:
        while True:
            prefix = f.read(4)
            if(prefix == b''):
                break
            if(len(prefix) != 4):
                break
            length = int.from_bytes(prefix, 'big')
            entry = f.read(length)
            if(len(entry) != length):
                break
            last_good_ofset = f.tell()
            entries.append(entry)
    return entries, last_good_ofset

def read_all_entries(path:str) -> list[bytes]:
    entries, ofset = _scan_entries(path)
    return entries

def recover(path:str) -> list[bytes]:
    if not os.path.exists(path):
        return []
    entries, ofset = _scan_entries(path)
    if( os.path.getsize(path) > ofset):
        with open(path, 'r+b') as f:
            f.truncate(ofset)
            os.fsync(f.fileno())
    return entries