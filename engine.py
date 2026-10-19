from wal import append_entry, recover
from records import encode_record, decode_record
from sstable import get_latest_seq, generate_padded_filepath, flush_memtable, build_index, get_from_sstable, get_all_sstables
from records import OP_DELETE, OP_SET, TOMBSTONE
import os

WAL_FILENAME = 'wal.log'
DEFAULT_MEMTABLE_LIMIT = 4 * 1024 * 1024

class Store:
    def __init__(self, directory, memtable_limit= DEFAULT_MEMTABLE_LIMIT):
        os.makedirs(directory, exist_ok=True)

        self.memtable = {}
        self.wal_path = os.path.join(directory, WAL_FILENAME)
        self.directory = directory
        self.seq_num = get_latest_seq(self.directory) # highest sequence number used so far; the next flush writes seq_num + 1
        sstable_paths = get_all_sstables(self.directory)
        self.sstable_list = []
        self.memtable_bytes = 0
        self.memtable_limit = memtable_limit
        raw_entries = recover(self.wal_path)

        for path in sstable_paths:
            index = build_index(path)
            self.sstable_list.append((path, index))

        for record in raw_entries:
            op_type, key, value = decode_record(record)
            if(op_type == OP_SET): #SET
                self._apply(key, value)
            elif op_type == OP_DELETE: #DELETE
                self._apply(key, TOMBSTONE)
            else:
                raise ValueError("Operation type not recognized") 

    def set(self, key, value):
        encoded_record = encode_record(OP_SET,key,value)
        append_entry(self.wal_path,encoded_record) # Add the instruction to the Wall
        self._apply(key, value)
        self._maybe_flush()

    def delete(self, key):
        encoded_record = encode_record(OP_DELETE,key) 
        append_entry(self.wal_path, encoded_record) # Add the instruction to the Wal
        self._apply(key, TOMBSTONE)
        self._maybe_flush()

    def get(self, key):
        # the key is on the memtable either with a value or as a deleted one, return accordingly 
        if key in self.memtable:
            if self.memtable[key] is TOMBSTONE:
                return None
            return self.memtable[key]
        # iterate over the reversed sstable_list, and for each check, if TOM return None, else return the value (value or None), nothing found, no key ever stored, return none 
        for (path, index) in reversed(self.sstable_list):
            value = get_from_sstable(path, index, key)
            if value is TOMBSTONE:
                return None 
            if value is not None:
                return value 
        
        return None

    def flush(self):
        if not self.memtable:
            return 
        new_seq = self.seq_num + 1
        new_path = generate_padded_filepath(self.directory, new_seq)
        flush_memtable(self.memtable, new_path)
        new_index = build_index(new_path)
        self.sstable_list.append((new_path, new_index))
        self.seq_num = new_seq
        self.memtable.clear()
        self.memtable_bytes = 0
        try:
            os.remove(self.wal_path)
        except FileNotFoundError:
            pass

    def _apply(self, key: bytes, value=TOMBSTONE):
        self.memtable[key] = value
        if value is TOMBSTONE:
            self.memtable_bytes += len(key) + 1
        else:
            self.memtable_bytes += len(key) + len(value)

    def _maybe_flush(self):
        if self.memtable_bytes >= self.memtable_limit:
            self.flush()