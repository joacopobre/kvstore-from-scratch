from engine import Store

s = Store('store_test.bin') # Store instance

# set some values 
s.set(b'x', b'1')
s.set(b'y', b'2')
s.set(b'z', b'3') 

# delete a value
s.delete(b'y')

# getting the values 

record = s.get(b'x')
assert record == b'1', 'SET round-trip FAILD'

record = s.get(b'y') # should return None thus not printing
assert record == None, 'DELETE round-trip FAILED'


s2 = Store('store_test.bin')  # a fresh instance — simulates a restart

record = s2.get(b'x')
assert record == b'1', 'Recovery FAILED for x'

record = s2.get(b'y')
assert record == None, 'Recovery FAILED — y should be deleted'

record = s2.get(b'z')
assert record == b'3', 'Recovery FAILED for z'

print("All Store recovery tests PASSED")