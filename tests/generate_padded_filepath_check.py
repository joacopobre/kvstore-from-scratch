



import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import generate_padded_filepath

result = generate_padded_filepath(directory='data', seq=2)
expect = os.path.join("data", "sstable_000002.bin")
assert result == expect
print('pass')

result = generate_padded_filepath(directory='data', seq=123456)
expect = os.path.join("data", "sstable_123456.bin")
assert result == expect
print('pass')

result = generate_padded_filepath(directory='data', seq=7)
expect = os.path.join("data", "sstable_000007.bin")
assert result == expect
print('pass')