import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Store

CRASH_CODE = 42

directory = sys.argv[1]
crash_at = sys.argv[2]
scenario = sys.argv[3] if len(sys.argv) > 3 else "flush"

real_rename = os.rename
real_remove = os.remove


def crash():
    os._exit(CRASH_CODE)


def install_crash(crash_at):
    if crash_at == "before_rename":
        def patched_rename(src, dst):
            crash()
        os.rename = patched_rename

    elif crash_at == "after_rename":
        def patched_rename(src, dst):
            real_rename(src, dst)
            crash()
        os.rename = patched_rename

    elif crash_at == "after_wal_removed":
        def patched_remove(path):
            real_remove(path)
            crash()
        os.remove = patched_remove

    elif crash_at.startswith("after_removes_"):
        limit = int(crash_at.split("_")[-1])
        count = {"n": 0}
        def patched_remove(path):
            real_remove(path)
            count["n"] += 1
            if count["n"] == limit:
                crash()
        os.remove = patched_remove


if scenario == "flush":
    install_crash(crash_at)
    s = Store(directory)
    s.set(b'k', b'1')
    s.set(b'j', b'2')
    s.delete(b'j')
    if crash_at == "after_writes":
        crash()
    s.flush()

elif scenario == "compact":
    s = Store(directory)
    s.set(b'a', b'1')
    s.set(b'b', b'2')
    s.flush()                  # file 1: a=1, b=2
    s.set(b'b', b'3')
    s.flush()                  # file 2: b=3
    s.delete(b'a')
    s.flush()                  # file 3: a=TOMBSTONE
    install_crash(crash_at)    # only now, so setup can't trigger the crash
    s.compact()