import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

CRASH_CODE = 42

directory = sys.argv[1]
crash_at = sys.argv[2]

real_rename = os.rename
real_remove = os.remove


def crash():
    os._exit(CRASH_CODE)          # no cleanup, no buffer flushing: as abrupt as it gets


if crash_at == "before_rename":
    def patched_rename(src, dst):
        crash()                    # the .tmp file is written, the rename never happens
    os.rename = patched_rename

elif crash_at == "after_rename":
    def patched_rename(src, dst):
        real_rename(src, dst)
        crash()                    # the SSTable exists, the WAL is not deleted yet
    os.rename = patched_rename

elif crash_at == "after_wal_removed":
    def patched_remove(path):
        real_remove(path)
        crash()                    # the WAL is gone: a clean state
    os.remove = patched_remove

s = Store(directory)
s.set(b'k', b'1')
s.set(b'j', b'2')
s.delete(b'j')

if crash_at == "after_writes":
    crash()                        # every write has returned, no flush has happened

s.flush()
# if we get here, the crash point was never reached