# kvstore-from-scratch — A Storage Engine Built From Scratch

A key-value storage engine built from first principles in Python — no database
libraries, no ORMs. The goal isn't to reinvent Postgres for its own sake, but
to genuinely understand what's happening underneath one: durability, on-disk
data structures, crash recovery, and concurrency correctness, rather than
just consuming those guarantees through a driver.

## Why this project

My previous projects (Next.js/Postgres apps, a NestJS microservices platform,
an AI-agent pipeline, a FastAPI RAG backend) all sit *on top of* infrastructure
like Postgres, Redis, and RabbitMQ. This project goes one layer down: building
the primitives those systems are made of, myself, and being able to defend
every decision in it.

## Status

🚧 In progress. Working so far: write-ahead log, in-memory write buffer
(memtable), deletes via tombstones, immutable on-disk sorted files (SSTables)
with an index, automatic flush by memtable size, compaction, and recovery on
startup. Next: crash-injection tests, then concurrency control.

## Usage

```python
from engine import Store

store = Store("data")          # directory is created if missing
store.set(b"name", b"joaquin")
store.get(b"name")             # b"joaquin"
store.delete(b"name")
store.get(b"name")             # None (deleted and missing look the same to callers)
```

Keys and values are `bytes`. The memtable limit (default 4 MB) and the
compaction threshold (default 4 files) can be passed to `Store(...)`.

## Roadmap

- [X] Write-Ahead Log — durable, append-only log using `fsync` for crash safety
- [X] Crash-safety hardening (torn/partial write detection)
- [X] In-memory write buffer
- [X] SET/DELETE/tombstone
- [X] Flushing to immutable on-disk sorted files
- [X] Automatic flush by memtable size
- [X] Reads across memory + disk
- [X] Compaction
- [ ] Full crash recovery (crash-injection tests for flush and compaction)
- [ ] Concurrency control
- [ ] Wire protocol / server
- [ ] Client + minimal web console
- [ ] Deployment

## Design notes

**Write-ahead log.** Each WAL entry is stored as a 4-byte big-endian length
prefix followed by the raw entry bytes, allowing entries to be read back and
split correctly without ambiguity. Durability is enforced by explicitly
flushing Python's internal buffer and calling `fsync()` before acknowledging a
write as successful — verified with a real crash-simulation test (`os._exit()`
immediately after a write, followed by a fresh read in a separate process run).
A torn entry at the end of the log is detected and truncated on recovery.

**Writes and reads.** Every `set`/`delete` is appended to the WAL first and
then applied to the in-memory memtable. A delete stores a tombstone, which
means "stop looking" for that key: `get` checks the memtable, then the
SSTables from newest to oldest, and the first file that mentions the key
decides the answer.

**SSTables.**
* Row format: `[outer length][op flag][key length][key][value]`. The op flag
  distinguishes a value from a tombstone, which is stored with an empty value.
* Each file has an in-memory index mapping every key (tombstones included) to
  its row offset.
* Flush is atomic: write a `.tmp` file, fsync it, rename it into place, then
  fsync the directory. A leftover `.tmp` file from a crash is ignored.
* Files are numbered (`sstable_000001.bin`). Newest wins, and the number is
  parsed as an integer, never sorted as text.
* The WAL is deleted only after the SSTable is durable. Replaying a stale WAL
  after a crash is harmless: replay is idempotent and newest-wins, so it only
  duplicates data.

**Flush trigger.** A byte counter (key + value sizes) that only ever adds,
shared by live writes and WAL replay so recovery reproduces the live value.
The default limit is 4 MB. The trade-off: overwritten keys are over-counted,
which means flushing slightly earlier than strictly needed, the safe
direction. If the replayed WAL is already over the limit at startup, the
store flushes before it opens, so the memtable is always under the limit once
a store is usable.

**Compaction.** When the number of SSTables reaches a threshold (default 4),
all files are merged into one new file with the next sequence number, keeping
only the newest version of each key and dropping tombstones. Old files are then
deleted **oldest first**. This order matters: a tombstone must outlive every
older file that still holds a value for its key, otherwise a deleted key
could come back if a crash left some old files behind. Tests build the
half-finished on-disk states a crash could leave and check that reads stay
correct in each, and that deleting in the wrong order does resurrect a key.

**Startup.** The store lists its directory to find SSTables (it never counts
upward, so gaps in numbering are harmless), rebuilds each file's index, then
replays the WAL into the memtable.

## Limitations

* Single-threaded, with no locking yet.
* A flush, and any compaction it triggers, run inside the `set`/`delete` that
  causes them, so that write is slow.
* Compaction rewrites all the data every time and loads it into memory; a
  streaming merge and tiered or levelled compaction would fix both.
* A lone SSTable is never compacted, so its tombstones stay on disk until a
  second file arrives.
* Each SSTable's full index is held in memory.
* Every write is fsynced individually (no batching), which favours durability
  over throughput.
* Crash behaviour during flush and compaction is verified by constructing the
  on-disk states a crash would leave, not yet by killing a live process
  mid-operation.

## Running the tests

Each test file in `tests/` is a standalone script:

```
python tests/<name>.py
```