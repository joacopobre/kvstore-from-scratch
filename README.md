# kvstore-from-scratch — A Storage Engine Built From Scratch

**Live demo: https://kvstore.joaquinrodes.dev** (the Console tab talks to the real database)

A key-value storage engine built from first principles in Python — no database
libraries, no ORMs. The goal isn't to reinvent Postgres for its own sake, but
to genuinely understand what's happening underneath one: durability, on-disk
data structures, crash recovery, and concurrency correctness, rather than
just consuming those guarantees through a driver.

## Why this project

My previous projects (Next.js/Postgres apps, an AI-agent pipeline, a FastAPI
RAG backend) all sit _on top of_ infrastructure like Postgres. This project
goes one layer down: building the primitives those systems are made of,
myself, and being able to defend every decision in it.

## Status

Complete and deployed. Working: write-ahead log, in-memory write buffer
(memtable), deletes via tombstones, immutable on-disk sorted files (SSTables)
with an index, automatic flush by memtable size, compaction, crash recovery
(tested by killing a real process mid-operation), thread-safe access, a TCP
server with a binary wire protocol, a Python client, a TypeScript client, a
small Node web server and a web console, deployed with Docker Compose behind
Caddy on a single VPS.

## Project layout

- Python storage engine, wire protocol, server and client: the repository root
  (`engine.py`, `server.py`, `protocol.py`, `client.py`, ...) and `tests/`.
- `web/`: the TypeScript side.
  - the TypeScript client for the wire protocol,
  - `src/app.ts`, a small Node server that exposes the store over HTTP
    (`/api/set`, `/api/get`, `/api/delete`) and serves the built site,
  - `site/`, the website (plain TypeScript, Vite and Tailwind).
- `Dockerfile.store`, `Dockerfile.web`, `docker-compose.yml`, `Caddyfile`:
  deployment.

## Usage

**As a library:**

```python
from engine import Store

store = Store("data")          # directory is created if missing
store.set(b"name", b"joaquin")
store.get(b"name")             # b"joaquin"
store.delete(b"name")
store.get(b"name")             # None (deleted and missing look the same to callers)
```

**As a server** (listens on `127.0.0.1:9000`, data in `data/`):

```
python server.py
```

```python
from client import KVClient

client = KVClient("127.0.0.1", 9000)
client.set(b"name", b"joaquin")
client.get(b"name")            # b"joaquin"
client.get(b"missing")         # None
client.delete(b"name")
client.close()
```

Keys and values are `bytes`. The memtable limit (default 4 MB) and the
compaction threshold (default 4 files) can be passed to `Store(...)`. A server
error is raised on the client as `ServerError`.

The store server reads its settings from environment variables: `KV_HOST`,
`KV_PORT` and `KV_DATA_DIR`.

**The whole thing, with Docker:**

```
docker compose up --build
```

Then open http://localhost. Compose starts three containers: the store, the
Node web app and Caddy. Only Caddy publishes ports; the store and the web app
are reachable only on Compose's private network, and the store's data lives in
a named volume.

**The web app without Docker** (from `web/`, with the store running):

```
pnpm install
pnpm vite build
pnpm exec tsx src/app.ts
```

It reads `STORE_HOST` (default `127.0.0.1`), `STORE_PORT` (default `9000`) and
`PORT` (default `3000`).

## The public demo

The live site is a real database that anyone can write to, so it is limited:

- keys up to 128 bytes, values up to 1,024 bytes, request bodies up to 64 KB;
- 60 requests per minute per IP address;
- a global budget of 2,000 requests per hour, after which the demo says it is
  at capacity;
- all data is wiped every day at 04:00 UTC by a scheduled job.

The rate limit and the budget are kept in the web app's memory, so they reset
when it restarts. The server is hardened: a non-root user, SSH keys only (no
passwords, no root login) and a firewall that allows only SSH, HTTP and HTTPS.

## Roadmap

- [x] Write-Ahead Log — durable, append-only log using `fsync` for crash safety
- [x] Crash-safety hardening (torn/partial trailing records detected and truncated)
- [x] In-memory write buffer
- [x] SET/DELETE/tombstone
- [x] Flushing to immutable on-disk sorted files
- [x] Automatic flush by memtable size
- [x] Reads across memory + disk
- [x] Compaction
- [x] Full crash recovery (crash-injection tests for flush and compaction)
- [x] Concurrency control
- [x] Wire protocol / server
- [x] Python client
- [x] TypeScript client
- [x] Web console
- [x] Deployment

## Design notes

**Write-ahead log.** Each WAL entry is stored as a 4-byte big-endian length
prefix followed by the raw entry bytes, allowing entries to be read back and
split correctly without ambiguity. Durability is enforced by explicitly
flushing Python's internal buffer and calling `fsync()` before acknowledging a
write as successful — verified with a real crash-simulation test (`os._exit()`
immediately after a write, followed by a fresh read in a separate process run).
A torn entry at the end of the log is detected and truncated on recovery.
Records carry no checksum, so a record that is complete but corrupted would not
be detected; the log only guards against an incomplete record at the end.

**Writes and reads.** Every `set`/`delete` is appended to the WAL first and
then applied to the in-memory memtable. A delete stores a tombstone, which
means "stop looking" for that key: `get` checks the memtable, then the
SSTables from newest to oldest, and the first file that mentions the key
decides the answer.

**SSTables.**

- Row format: `[outer length][op flag][key length][key][value]`. The op flag
  distinguishes a value from a tombstone, which is stored with an empty value.
- Each file has an in-memory index mapping every key (tombstones included) to
  its row offset.
- Flush is atomic: write a `.tmp` file, fsync it, rename it into place, then
  fsync the directory. A leftover `.tmp` file from a crash is ignored.
- Files are numbered (`sstable_000001.bin`). Newest wins, and the number is
  parsed as an integer, never sorted as text.
- The WAL is deleted only after the SSTable is durable. Replaying a stale WAL
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
correct in each, that deleting in the wrong order does resurrect a key, and
a real child process is killed at each step of the delete sequence to check the
real code behaves the same.

**Startup.** The store lists its directory to find SSTables (it never counts
upward, so gaps in numbering are harmless), rebuilds each file's index, then
replays the WAL into the memtable.

**Concurrency.** One `RLock` per `Store` keeps threads from interleaving. It's
an `RLock` because `set` calls `flush`, which can call `compact`. The WAL
append and the memtable update sit in the same critical section so both orders
always agree. A concurrency test with several writers and readers and tiny
limits (so flushes and compactions happen constantly) fails without the lock
and passes with it.

**Wire protocol.** A binary, length-prefixed protocol over TCP. Every message
is framed as `[4-byte length][payload]`, where the length counts only the
payload.

- Request payload: `[1B command][4B key length][key][value]`, with commands
  for SET, GET and DELETE.
- Response payload: `[1B status][body]`, with statuses OK, NOT_FOUND and ERROR.
  A successful GET carries the value as the body, and an ERROR carries a short
  message.
- TCP is a byte stream with no message boundaries, so `read_message` uses
  `recv_exact` to read exactly the 4-byte length and then exactly that many
  bytes, however the data is split across packets.
- Because every field's size is written before it, keys and values can contain
  any bytes (including zero bytes and bytes that look like protocol framing).
- A length received from the network is never trusted: messages over 16 MB are
  rejected before any body is read, so a client cannot make the server
  allocate arbitrary memory.
- Encoding and decoding are pure functions, tested with hand-computed bytes.

**Server.** One thread per connection, all sharing a single `Store`, so the
store's lock is what keeps concurrent clients correct. A malformed request is
answered with an ERROR response and the connection stays open. An oversized
length prefix gets an ERROR response and the connection is closed, because the
stream can no longer be trusted. If the store itself raises, the client gets a
generic error and the real exception is logged on the server side. Ctrl+C
closes the listener and flushes the memtable.

**Web layer.** The TypeScript client speaks the same wire protocol from Node.
The Node app validates input, applies the demo limits and translates between
HTTP and the store: `POST /api/set` and `/api/delete` take JSON bodies,
`GET /api/get?key=...` returns the value or a 404. It also serves the built
site, with HTTP Range support so the demo videos play in Safari.

## Limitations

- A single coarse lock serialises everything, including reads, so a long flush
  or compaction blocks every client. The lock protects threads, not processes:
  two processes opening the same data directory would corrupt each other.
  Concurrency tests are probabilistic and can show a race, not prove its
  absence.
- A flush, and any compaction it triggers, run inside the `set`/`delete` that
  causes them, so that write is slow.
- Compaction rewrites all the data every time and loads it into memory; a
  streaming merge and tiered or levelled compaction would fix both.
- A lone SSTable is never compacted, so its tombstones stay on disk until a
  second file arrives.
- Each SSTable's full index is held in memory.
- Every write is fsynced individually (no batching), which favours durability
  over throughput.
- Log records have no checksums, so corruption in the middle of a record (as
  opposed to a record cut short at the end) is not detected.
- Crash tests kill the **process** (`os._exit`), not the **power**. The OS still
  flushes its cache after a process kill, so these tests verify ordering and
  atomicity of the on-disk steps, but not `fsync` correctness; that is
  reasoned, not tested.
- The store server has no authentication or encryption, and no limit on the
  number of connections (one thread each). In the deployment only the Node app
  can reach it.
- It is a single node with no replication.
- `KVClient` wraps a single socket and is not safe to share between threads;
  use one client per thread.
- The web console sends and shows text only, although the protocol carries raw
  bytes.
- There is no way to list or scan keys, only get/set/delete by exact key.

## Running the tests

```
pytest
```

The suite includes unit tests with hand-computed bytes, tests over real TCP
connections, and crash tests that launch a child process and kill it
(`os._exit`) at chosen points in a flush or a compaction, then reopen the data
directory and check what survived.
