import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from records import OP_DELETE, OP_SET
from utils.encode_entry import encode_sstable_entry


result = encode_sstable_entry(OP_SET, b"x", b"1")

outer = b"\x00\x00\x00\x07"   # inner part is 7 bytes
flag = b"\x00"                # this is the OP_SET value in hex. Make sure it matches OP_SET
key_length = b"\x00\x00\x00\x01"   # b"x" is 1 byte
expected = outer + flag + key_length + b"x" + b"1"

assert result == expected, 'failed'
print('set case pass')

result = encode_sstable_entry(OP_DELETE, b"x")   # no value argument

outer = b"\x00\x00\x00\x06"   # inner part is 6 bytes
flag = b"\x01"                # this is the OP_DELETE value in hex. Make sure it matches OP_DELETE
key_length = b"\x00\x00\x00\x01"   # b"x" is 1 byte
expected = outer + flag + key_length + b"x"

assert result == expected, 'failed'
print('tombstone case pass')

result = encode_sstable_entry(OP_SET, b"abc", b"")

outer = b"\x00\x00\x00\x08"  
flag = b"\x00"                
key_length = b"\x00\x00\x00\x03"  
expected = outer + flag + key_length + b"abc"

assert result == expected, 'failed'
print('All pass')