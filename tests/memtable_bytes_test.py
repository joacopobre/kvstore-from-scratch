import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

with tempfile.TemporaryDirectory() as directory:
    s = Store(directory)

    s.set(b'x', b'hello')
    s.set(b'a', b'hellou')
    s.delete(b'a')

    expected = (len(b'x') + len(b'hello')) \
         + (len(b'a') + len(b'hellou')) \
         + (len(b'a') + 1)

    
    assert s.memtable_bytes == expected

    s2 = Store(directory)

    assert s2.memtable_bytes == expected

    s2.flush()

    assert s2.memtable_bytes == 0

    s2.set(b'k', b'vv')
    assert s2.memtable_bytes == len(b'k') + len(b'vv')