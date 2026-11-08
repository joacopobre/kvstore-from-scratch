import net from 'node:net'

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
      const bytes = typeof chunk === 'string' ? Buffer.from(chunk) : chunk
      this.queue.push(bytes)
      this.trySatisfy()
    })
    socket.on('close', () => {
      const order = this.pending
      if (order == null) return
      this.pending = null
      order.reject(new Error('connection closed'))
    })
  }

  read(n: number): Promise<Buffer> {
    return new Promise((resolve, reject) => {
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
  }
}
export { SocketReader }
