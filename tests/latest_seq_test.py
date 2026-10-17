

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sstable import get_latest_seq
with tempfile.TemporaryDirectory() as directory:
    # directory is a string, a real folder that exists right now
    open(os.path.join(directory, "hello.txt"), "wb").close()   # makes an empty file
    print(os.listdir(directory))   # ['hello.txt']
    result = get_latest_seq(directory)
    assert result == 0 
    print('pass')


with tempfile.TemporaryDirectory() as directory:
    # directory is a string, a real folder that exists right now
    open(os.path.join(directory, "sstable_000001.bin"), "wb").close()   # makes an empty file
    open(os.path.join(directory, "sstable_000030.bin"), "wb").close()   # makes an empty file
    open(os.path.join(directory, "sstable_000020.bin"), "wb").close()   # makes an empty file
    print(os.listdir(directory))  
    result = get_latest_seq(directory)
    assert result == 30
    print('pass')


with tempfile.TemporaryDirectory() as directory:
    # directory is a string, a real folder that exists right now
    open(os.path.join(directory, "sstable_000001.bin"), "wb").close()   # makes an empty file
    open(os.path.join(directory, "sstable_000030.bin"), "wb").close()   # makes an empty file
    open(os.path.join(directory, "sstable_000005.bin.tmp"), "wb").close()   # makes an empty file
    print(os.listdir(directory))  
    result = get_latest_seq(directory)
    assert result == 30
    print('pass')





