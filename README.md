# kvstore_from_scrach — A Storage Engine Built From Scratch

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

🚧 Early / in progress. WAL, memtable, tombstones, SSTables with an index, automatic flush by size, and startup recovery.

## Roadmap

- [X] Write-Ahead Log — durable, append-only log using `fsync` for crash safety
- [X] Crash-safety hardening (torn/partial write detection)
- [X] In-memory write buffer
- [X] SET/DELETE/tombstone
- [X] Flushing to immutable on-disk sorted files
- [ ] Compaction
- [X] Automatic flush by memtable size
- [X] Reads across memory + disk
- [ ] Full crash recovery via WAL replay
- [ ] Concurrency control
- [ ] Wire protocol / server
- [ ] Client + minimal web console
- [ ] Deployment

## Design notes

Each WAL entry is stored as a 4-byte big-endian length prefix followed by the
raw entry bytes, allowing entries to be read back and split correctly without
ambiguity. Durability is enforced by explicitly flushing Python's internal
buffer and calling `fsync()` before acknowledging a write as successful —
verified with a real crash-simulation test (`os._exit()` immediately after a
write, followed by a fresh read in a separate process run).

* SSTable row format: `[outer length][op flag][key length][key][value]`.
* Flush is atomic: write a `.tmp` file, fsync, rename, then fsync the directory.
* Newest wins: files are numbered, read newest to oldest, and the number is parsed as an integer, never sorted as text.
* The flush trigger: a byte counter that only adds, shared by live writes and replay, with a default of 4 MB.
* State the trade-off: overwrites are over-counted, which means earlier flushes, the safe direction.

## Limitations
* Single-threaded, with no locking yet.
* A flush runs inside the set that triggers it, so write is slow.
* No compaction yet, so reads slow down as files accumulate and tombstones aren’t reclaimed.
* Each SSTable’s full index is held in memory.

