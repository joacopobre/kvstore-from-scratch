
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sstable import merge_tables
from records import TOMBSTONE

tables = [{b'a':b'1',b'b':b'2',b'c':b'3' },{b'b':b'20', b'd':b'4'},{b'a':TOMBSTONE, b'e':b'5'}]

result = merge_tables(tables, False)
expected = {b'a': TOMBSTONE, b'b': b'20', b'c': b'3', b'd': b'4', b'e': b'5'}
assert result == expected

result = merge_tables(tables, True)
expected = {b'b': b'20', b'c': b'3', b'd': b'4', b'e': b'5'}
assert result == expected
