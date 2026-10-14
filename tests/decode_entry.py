import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from records import OP_DELETE, OP_SET

from utils.decode_entry import decode_sstable_entry



flag       = b"\x00"              # OP_SET is 0
key_length = b"\x00\x00\x00\x01"  # the key is 1 byte long
data = flag + key_length + b"x" + b"1"

result = decode_sstable_entry(data)

assert result == (OP_SET, b"x", b"1")
print("PASSED")

# Tombstone
flag       = b"\x01"              
key_length = b"\x00\x00\x00\x01"  
data = flag + key_length + b"x" + b""

result = decode_sstable_entry(data)

assert result == (OP_DELETE, b"x", b"")
print("PASSED")

#

flag       = b"\x00"              
key_length = b"\x00\x00\x00\x03"  
data = flag + key_length + b"abc" + b""

result = decode_sstable_entry(data)

assert result == (OP_SET, b"abc", b"")
print("PASSED")