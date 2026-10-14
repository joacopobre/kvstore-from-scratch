from wal import append_entry, recover
from records import encode_record, decode_record
from records import OP_DELETE, OP_SET, TOMBSTONE


class Store:
    def __init__(self, path):
        self.memtable = {}
        self.path = path
        raw_entries = recover(path)
        

        for record in raw_entries:
            op_type, key, value = decode_record(record)
            if(op_type == OP_SET): #SET
                self.memtable[key] = value
            elif op_type == OP_DELETE: #DELETE
                self.memtable[key] = TOMBSTONE
            else:
                raise Exception("Operation type not recognized") 

    def set(self, key, value):
        encoded_record = encode_record(OP_SET,key,value)
        append_entry(self.path,encoded_record) # Add the instruction to the Wall
        self.memtable[key] = value # update the memtable, set the key to the value 

    def delete(self, key):
        encoded_record = encode_record(OP_DELETE,key) 
        append_entry(self.path, encoded_record) # Add the instruction to the Wal
        self.memtable[key] = TOMBSTONE

    def get(self, key):
        if key not in self.memtable:
            return None 
        value = self.memtable.get(key)
        if value is TOMBSTONE:
            return None 
        return value 
