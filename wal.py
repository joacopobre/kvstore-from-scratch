import os 

def append_entry(path:str, data:bytes)->None:
    with open(path, 'ab') as f:
        length = len(data)
        len_prefix = length.to_bytes(4, 'big')
        f.write(len_prefix + data)
        f.flush()
        os.fsync(f.fileno())

def read_all_entries(path:str) -> list[bytes]:
    entries = []
    with open(path, 'rb')as f:
        while True:
            prefix = f.read(4)
            if(prefix == b''):
                break
            length = int.from_bytes(prefix, 'big')
            entry = f.read(length)
            entries.append(entry)
    return entries
