


def encode_sstable_entry(key: bytes, value: bytes) -> bytes:
    KEY_LEN_SIZE = 4
    key_length = len(key).to_bytes(KEY_LEN_SIZE, 'big')
    inner = key_length + key + value
    outer_length = len(inner).to_bytes(KEY_LEN_SIZE, 'big')
    
    return outer_length + inner