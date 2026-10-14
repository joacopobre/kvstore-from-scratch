from utils.encode_entry import OP_SIZE, KEY_LEN_SIZE

def decode_sstable_entry(data: bytes) -> tuple[int,bytes, bytes]:
    byte_op = data[0:OP_SIZE]
    op_type = int.from_bytes(byte_op, 'big')
    key_len = data[OP_SIZE : OP_SIZE + KEY_LEN_SIZE]
    key_len_int = int.from_bytes(key_len, 'big')
    key = data[OP_SIZE + KEY_LEN_SIZE : OP_SIZE + KEY_LEN_SIZE + key_len_int]
    value = data[OP_SIZE + KEY_LEN_SIZE + key_len_int :]
    return op_type, key, value