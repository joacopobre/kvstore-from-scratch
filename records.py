

def encode_record(op_value: int, key: bytes, value: bytes =b"") -> bytes:
    byte_op = op_value.to_bytes(1, 'big')
    key_len_prefix = len(key).to_bytes(4, 'big')

    return byte_op + key_len_prefix + key + value

def decode_record(record: bytes) -> tuple[int,bytes,bytes]:
    OP_SIZE = 1
    KEY_LEN_SIZE = 4 

    operation = record[0:OP_SIZE] # first byte for operation
    op_type = int.from_bytes(operation, 'big') # make it an int (0 or 1) = (SET or DELETE)
    length = record[OP_SIZE : OP_SIZE + KEY_LEN_SIZE] # key lenght in bytes
    key_length = int.from_bytes(length, 'big') # pass that length to int
    key_bytes = record[OP_SIZE + KEY_LEN_SIZE: OP_SIZE + KEY_LEN_SIZE + key_length]
    value = record[OP_SIZE + KEY_LEN_SIZE + key_length :]

    return op_type, key_bytes, value
