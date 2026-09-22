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

🚧 Early / in progress. Currently working through the durability layer
(Write-Ahead Log). Being built incrementally — each stage is implemented only
after understanding the concept behind it, not copied from a reference
implementation.

## Roadmap

- [x] Write-Ahead Log — durable, append-only log using `fsync` for crash safety
- [ ] Crash-safety hardening (torn/partial write detection)
- [ ] In-memory write buffer
- [ ] Flushing to immutable on-disk sorted files
- [ ] Compaction
- [ ] Reads across memory + disk
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