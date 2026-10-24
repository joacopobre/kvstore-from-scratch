import threading
import traceback

from engine import Store

WRITERS = 4
READERS = 2
KEYS_PER_WRITER = 200


def make_key(worker_id, i):
    return f"w{worker_id}-{i}".encode()


def make_value(worker_id, i):
    return f"value-{worker_id}-{i}".encode()


def find_missing(store):
    return [
        make_key(w, i)
        for w in range(WRITERS)
        for i in range(KEYS_PER_WRITER)
        if store.get(make_key(w, i)) != make_value(w, i)
    ]


def test_concurrent_writers_and_readers(tmp_path):
    directory = str(tmp_path)
    s = Store(directory, memtable_limit=64, compaction_threshold=3)
    errors = []

    def writer(worker_id):
        try:
            for i in range(KEYS_PER_WRITER):
                s.set(make_key(worker_id, i), make_value(worker_id, i))
        except Exception as e:
            errors.append(traceback.format_exc())

    def reader():
        try:
            for i in range(KEYS_PER_WRITER):
                s.get(make_key(0, 0))
        except Exception as e:
            errors.append(traceback.format_exc())

    # TODO: create WRITERS writer threads (target=writer, args=(worker_id,))
    #       and READERS reader threads (target=reader), start them all, join them all

    t1 = threading.Thread(target=writer, args=(0,))
    t2 = threading.Thread(target=writer, args=(1,))
    t3 = threading.Thread(target=writer, args=(2,))
    t4 = threading.Thread(target=writer, args=(3,))
    t5 = threading.Thread(target=reader)
    t6 = threading.Thread(target=reader)
   

    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    assert errors == []
    assert find_missing(s) == []

    s2 = Store(directory)               # reopen from disk
    assert find_missing(s2) == []

    