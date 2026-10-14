
LENGTH_SIZE = 4

def encode_sstable_entry(op_type: int, key: bytes, value: bytes = b"") -> bytes:
    
    byte_op = op_type.to_bytes(1, 'big')
    key_length = len(key).to_bytes(LENGTH_SIZE, 'big')
    inner =  byte_op + key_length + key + value 
    outer_length = len(inner).to_bytes(LENGTH_SIZE, 'big')
    
    return outer_length + inner