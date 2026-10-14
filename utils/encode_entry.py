OP_SIZE = 1
KEY_LEN_SIZE = 4

def encode_sstable_entry(op_type: int, key: bytes, value: bytes = b"") -> bytes:
    
    byte_op = op_type.to_bytes(OP_SIZE, 'big')
    key_length = len(key).to_bytes(KEY_LEN_SIZE, 'big')
    inner =  byte_op + key_length + key + value 
    outer_length = len(inner).to_bytes(KEY_LEN_SIZE, 'big')
    
    return outer_length + inner