from wal import append_entry, recover
from records import encode_record, decode_record

class Store:
    def __init__(self, path):
        self.memtable = {}
        self.path = path
        raw_entries = recover(path)

        for record in raw_entries:
            op_type, key_bytes, value = decode_record(record)
            if(op_type == 0): #SET
                self.memtable[key_bytes] = value
            else: #DELETE
                if(key_bytes in self.memtable):
                    self.memtable.pop(key_bytes)

    def set(self, key, value):
        encoded_record = encode_record(0,key,value)
        append_entry(self.path,encoded_record) # Add the instruction to the Wall
        self.memtable[key] = value # update the memtable, set the key to the value 

    def delete(self, key):
        encoded_record = encode_record(1,key) 
        append_entry(self.path, encoded_record) # Add the instruction to the Wall
        if(key in self.memtable): # deliverate decision, no key nothing happens, the inteded outcome holds, that key is not on the table 
            self.memtable.pop(key) # update the memtable, delete the key

    def get(self, key):
        return self.memtable.get(key)