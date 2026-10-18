import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

with tempfile.TemporaryDirectory() as directory:
    s = Store(directory)

    s.set(b'x', b'1')
    s.set(b'y', b'2')
    s.set(b'z', b'3') 

    s.delete(b'y')
    s.flush()

    s.set(b'x', b'4')
    s.flush()

    s2 = Store(directory)
    assert s2.get(b'x') == b'4'
    assert s2.get(b'z') == b'3'
    assert s2.get(b'y') == None

    assert len(s2.sstable_list) == 2
    assert s2.seq_num == 2 

    print('PASSED')