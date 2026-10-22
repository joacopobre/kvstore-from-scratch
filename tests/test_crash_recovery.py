import os
import sys
import subprocess
import pytest 

from engine import Store, WAL_FILENAME
from sstable import get_all_sstables
from records import TOMBSTONE

CHILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_child.py")
CRASH_CODE = 42


def run_child(directory, crash_at, run_child):
    result = subprocess.run(
        [sys.executable, CHILD, directory, crash_at],
        capture_output=True, text=True,
    )
    # if the child exited normally, the crash point was never reached
    # and the test would prove nothing
    assert result.returncode == CRASH_CODE, result.stderr


def wal_exists(directory):
    return os.path.exists(os.path.join(directory, WAL_FILENAME))


def has_tmp_file(directory):
    return any(name.endswith('.tmp') for name in os.listdir(directory))


def assert_recovered(directory):
    s = Store(directory)
    assert s.get(b'k') == b'1'
    assert s.get(b'j') is None
    return s


def test_crash_after_writes_before_flush(tmp_path):
    directory = str(tmp_path)
    run_child(directory, "after_writes")

    
    assert get_all_sstables(directory) == []
    assert wal_exists(directory)
    s = assert_recovered(directory)
    assert s.memtable == {b'k': b'1', b'j': TOMBSTONE}


def test_crash_before_rename(tmp_path):
    directory = str(tmp_path)
    run_child(directory, "before_rename")

    
    assert has_tmp_file(directory) 
    assert get_all_sstables(directory) == []
    assert wal_exists(directory) 
    s = assert_recovered(directory)
    
    assert len(s.sstable_list) == 0
    
    s.set(b'r', b't')
    s.flush()
    assert len(get_all_sstables(directory)) == 1    # the new flush produced a real SSTable
    assert not has_tmp_file(directory)              # the leftover .tmp was reused and renamed away
    assert not wal_exists(directory)                # flush finished, so the WAL is gone

    assert s.get(b'r') == b't'
    assert s.get(b'k') == b'1'
    assert s.get(b'j') is None



def test_crash_after_rename_before_wal_removed(tmp_path):
    directory = str(tmp_path)
    run_child(directory, "after_rename")

   
    assert len(get_all_sstables(directory)) == 1
    assert wal_exists(directory) 
    s = assert_recovered(directory)
   
    assert len(s.sstable_list) == 1
    assert s.memtable == {b'k': b'1', b'j': TOMBSTONE}
    assert s.get(b'k') == b'1'
    assert s.get(b'j') is None


def test_crash_after_wal_removed(tmp_path):
    directory = str(tmp_path)
    run_child(directory, "after_wal_removed")

    
    assert len(get_all_sstables(directory)) == 1
    assert not wal_exists(directory) 
    s = assert_recovered(directory)
   
    assert len(s.memtable) == 0
    
    assert s.get(b'k') == b'1'
    assert s.get(b'j') is None

def run_child(directory, crash_at, scenario="flush"):
    result = subprocess.run(
        [sys.executable, CHILD, directory, crash_at, scenario],
        capture_output=True, text=True,
    )
    assert result.returncode == CRASH_CODE, result.stderr


def assert_compact_recovered(directory):
    s = Store(directory)
    assert s.get(b'a') is None
    assert s.get(b'b') == b'3'
    return s


def sstable_names(directory):
    return [os.path.basename(p) for p in get_all_sstables(directory)]


def test_crash_compact_after_merged_file_written(tmp_path):
    directory = str(tmp_path)
    run_child(directory, "after_rename", "compact")

    # TODO: assert the 4 file names on disk (old files 1-3 plus the merged file 4)
    assert_compact_recovered(directory)


@pytest.mark.parametrize("removed, expected_names", [
    (1, ['sstable_000002.bin', 'sstable_000003.bin', 'sstable_000004.bin']),
    (2, ['sstable_000003.bin', 'sstable_000004.bin']),
    (3, ['sstable_000004.bin']),
])
def test_crash_compact_during_deletes(tmp_path, removed, expected_names):
    directory = str(tmp_path)
    run_child(directory, f"after_removes_{removed}", "compact")

    assert sstable_names(directory) == expected_names
    assert_compact_recovered(directory)