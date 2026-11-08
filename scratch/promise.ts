import net from 'node:net'

const STATUS_OK = 0
const STATUS_NOT_FOUND = 1

import {
  CMD_GET,
  CMD_SET,
  CMD_DEL,
  encodeRequest,
  decodeResponse
} from './encode'
class ByteQueue {
  private buffered: Buffer = Buffer.alloc(0)

  push(chunk: Buffer): void {
    this.buffered = Buffer.concat([this.buffered, chunk])
  }

  take(n: number): Buffer | null {
    if (this.buffered.length < n) return null

    const result = this.buffered.subarray(0, n)
    this.buffered = this.buffered.slice(n)
    return result
  }
}

class SocketReader {
  private queue = new ByteQueue()
  private pending: {
    n: number
    resolve: (bytes: Buffer) => void
    reject: (err: Error) => void
  } | null = null

  constructor(socket: net.Socket) {
    socket.on('data', (chunk) => {
      // TODO 1: push the chunk into the queue, then try to satisfy the pending read
      this.queue.push(chunk)
      this.trySatisfy()
    })
    socket.on('close', () => {
      // TODO 2: if a read is pending, reject it with new Error("connection closed")
      const order = this.pending
      if (order == null) return
      this.pending = null
      order.reject(new Error('connection closed'))
    })
  }

  read(n: number): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      // TODO 3: remember this request in this.pending, then try to satisfy it
      this.pending = { n, resolve, reject }
      this.trySatisfy()
    })
  }

  private trySatisfy(): void {
    const order = this.pending
    if (order === null) return
    const bytes = this.queue.take(order.n)
    if (bytes === null) return
    this.pending = null
    order.resolve(bytes)
    // TODO 4: if there's a pending read and the queue can supply its n bytes,
    // clear pending, then call its resolve with those bytes
  }
}

class ServerError extends Error {}

class KVClient {
  private socket: net.Socket
  private reader: SocketReader

  constructor(socket: net.Socket) {
    this.socket = socket
    this.reader = new SocketReader(socket)
  }

  private async request(
    command: number,
    key: Buffer,
    value?: Buffer
  ): Promise<{ status: number; body: Buffer }> {
    const encodedRequest = encodeRequest(command, key, value)
    this.socket.write(encodedRequest)
    const prefix = await this.reader.read(4)
    const length = prefix.readUInt32BE(0)
    const payload = await this.reader.read(length)
    return decodeResponse(payload)
  }
  static connect(host: string, port: number): Promise<KVClient> {
  return new Promise((resolve, reject) => {
    const socket = net.connect(port, host);
    
    socket.once("connect", ()=> {
        resolve(new KVClient(socket))
    })
    
    socket.once("error", (err) => {
        reject(err)
    })

  });
}

  async set(key: Buffer, value: Buffer): Promise<void> {
    const { status, body } = await this.request(CMD_SET, key, value)
    if (status !== STATUS_OK) {
      throw new ServerError(body.toString())
    }
  }

  async get(key: Buffer): Promise<Buffer | null> {
    const { status, body } = await this.request(CMD_GET, key)
    if (status === STATUS_OK) {
      return body
    }
    if (status === STATUS_NOT_FOUND) {
      return null
    }
    
    throw new ServerError(body.toString())
  }

  async delete(key: Buffer): Promise<void> {
    const { status, body } = await this.request(CMD_DEL, key)
    if (status !== STATUS_OK) {
      throw new ServerError(body.toString())
    }
  }

  close(): void {
    this.socket.end()
  }
}

async function demo() {
  try {
    const client = await KVClient.connect("127.0.0.1", 9000);
    await client.set(Buffer.from("city"), Buffer.from("salford"));
    console.log((await client.get(Buffer.from("city")))?.toString());
    client.close();
  } catch (e) {
    console.log("failed:", (e as Error).message);
  }
}
demo();
