

def decode_sstable_entry(data: bytes) -> tuple[bytes, bytes]:
    key_len = data[0 : 4]
    key_len_int = int.from_bytes(key_len, 'big')
    key = data[4 : 4 + key_len_int]
    value = data[4 + key_len_int :]
    return [key, value]