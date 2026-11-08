import {
  CMD_DEL,
  CMD_GET,
  CMD_SET,
  STATUS_OK,
  STATUS_NOT_FOUND,
  encodeRequest,
  decodeResponse,
} from './protocol'
import net from 'node:net'
import { SocketReader } from './reader'

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
      const socket = net.connect(port, host)

      socket.once('connect', () => {
        resolve(new KVClient(socket))
      })

      socket.once('error', (err) => {
        reject(err)
      })
    })
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
export {KVClient}