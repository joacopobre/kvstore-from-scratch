import os
from wal import append_entry, read_all_entries,recover

# --- Test 1: clean file, multiple entries ---
if os.path.exists('clean.bin'):
    os.remove('clean.bin')

append_entry('clean.bin', b"hello")
append_entry('clean.bin', b"world")
append_entry('clean.bin', b"foo")

result = read_all_entries('clean.bin')
print("Clean file result:", result)
assert result == [b"hello", b"world", b"foo"], "Clean file test FAILED"
print("Clean file test PASSED")

# --- Test 2: torn entry (simulates a crash mid-write) ---
if os.path.exists('torn.bin'):
    os.remove('torn.bin')


append_entry('torn.bin', b"one")
append_entry('torn.bin', b"two")
with open('torn.bin', 'ab') as f:
    f.write((5).to_bytes(4, 'big'))  # claims 5 bytes are coming
    f.write(b"he")                    # but only writes 2

print("size of the file befroe recover: ", os.path.getsize('torn.bin'))
recover('torn.bin')
print("size of the file after recover: ", os.path.getsize('torn.bin'))

result = read_all_entries('torn.bin')
print("Torn file result:", result)
assert result == [b"one", b"two"], "Torn file test FAILED"
print("Torn file test PASSED")