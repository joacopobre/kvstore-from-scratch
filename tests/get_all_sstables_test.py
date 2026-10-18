import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sstable import get_all_sstables

with tempfile.TemporaryDirectory() as directory:
    for name in ["sstable_000003.bin", "sstable_000001.bin",'sstable_999999.bin','sstable_1000000.bin', "sstable_000002.bin", "wal.log"]:
        open(os.path.join(directory, name), "wb").close()

    result = get_all_sstables(directory)
    
    expected = [
        os.path.join(directory, "sstable_000001.bin"),
        os.path.join(directory, "sstable_000002.bin"),
        os.path.join(directory, "sstable_000003.bin"),
        os.path.join(directory, "sstable_999999.bin"),
        os.path.join(directory, "sstable_1000000.bin"),
    ]
    assert result == expected
    print("PASSED order and noise")
    