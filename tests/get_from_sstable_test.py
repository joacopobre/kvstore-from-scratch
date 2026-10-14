

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from records import TOMBSTONE
from sstable import flush_memtable, build_index, get_from_sstable

path = 'get_test.bin'
flush_memtable({b"a": b"1", b"b": TOMBSTONE}, path)
index = build_index(path)

# 1. a real value comes back as bytes
assert get_from_sstable(path, index, b"a") == b"1"
print("PASSED value")


# 2. TODO: lookup of b"b" should be TOMBSTONE (use `is`, not ==)
assert get_from_sstable(path, index, b"b") is TOMBSTONE
print("PASSED value")

# 3. TODO: lookup of b"z" (not in the file) should be None,
#    and also assert it is NOT TOMBSTONE
assert get_from_sstable(path, index, b"z") is None
print("PASSED value")

# 4. TODO: look the keys up in scrambled order (b, then a, then z)
#    and check the three answers are the same as before
assert get_from_sstable(path, index, b"b") is TOMBSTONE
print("PASSED value")
assert get_from_sstable(path, index, b"a") == b"1"
print("PASSED value")
assert get_from_sstable(path, index, b"z") is None
print("PASSED value")