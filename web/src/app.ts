import http from 'node:http'
import { KVClient } from '../client'
import { send } from 'node:process'
import { buffer } from 'node:stream/consumers'
import { read } from 'node:fs'

const STORE_HOST = '127.0.0.1'
const STORE_PORT = 9000
const MAX_BODY = 64 * 1024 // 64 KB

function sendJson(
  res: http.ServerResponse,
  status: number,
  body: unknown
): void {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(body))
}
async function readBody(req: http.IncomingMessage): Promise<Buffer> {
  const chunks: Buffer[] = []
  let currBody = 0
  for await (const chunk of req) {
    currBody += chunk.length
    if (currBody > MAX_BODY) {
      throw new Error('body too large')
    }
    chunks.push(chunk)
  }
  return Buffer.concat(chunks)
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', 'http://localhost')

  if (req.method === 'POST' && url.pathname === '/set') {
    let body: Buffer
    try {
      body = await readBody(req)
    } catch {
      sendJson(res, 413, { error: 'body too large' })
      return
    }
    let data
    try {
      data = JSON.parse(body.toString())
    } catch {
      sendJson(res, 400, { error: 'invalid JSON' })
      return
    }

    if (data !== null) {
      if (typeof data.key !== 'string' || data.key === '') {
        sendJson(res, 400, { error: 'key must be string' })
        return
      }
      if (typeof data.value !== 'string') {
        sendJson(res, 400, { error: 'value must be string' })
        return
      }
    } else {
      sendJson(res, 400, { error: 'no data' })
      return
    }
    try {
      const client = await KVClient.connect(STORE_HOST, STORE_PORT)
      try {
        await client.set(Buffer.from(data.key), Buffer.from(data.value))
        sendJson(res, 200, { ok: true })
      } finally {
        client.close()
      }
    } catch (err) {
      console.log(err)
      sendJson(res, 502, { error: 'store unavailable' })
    }
    return
  }

  if (req.method === 'POST' && url.pathname === '/delete') {
    let body: Buffer
    try {
      body = await readBody(req)
    } catch {
      sendJson(res, 413, { error: 'body too large' })
      return
    }
    let data
    try {
      data = JSON.parse(body.toString())
    } catch {
      sendJson(res, 400, { error: 'invalid JSON' })
      return
    }
    if (data !== null) {
      if (typeof data.key !== 'string' || data.key === '') {
        sendJson(res, 400, { error: 'key must be a string' })
        return
      }
    } else {
      sendJson(res, 400, { error: 'no data' })
      return
    }
    try {
      const client = await KVClient.connect(STORE_HOST, STORE_PORT)
      try {
        await client.delete(Buffer.from(data.key))
        sendJson(res, 200, { ok: true })
      } finally {
        client.close()
      }
    } catch (err) {
      console.log(err)
      sendJson(res, 502, { error: 'server unavailable' })
    }
    return
  }

  if (req.method === 'GET' && url.pathname === '/get') {
    const key = url.searchParams.get('key')
    if (!key) {
      sendJson(res, 400, { error: 'missing key' })
      return
    }

    try {
      const client = await KVClient.connect(STORE_HOST, STORE_PORT)
      try {
        const value = await client.get(Buffer.from(key))
        if (value === null) {
          sendJson(res, 404, { error: 'not found' })
        } else {
          sendJson(res, 200, { value: value.toString() })
        }
      } finally {
        client.close()
      }
    } catch (err) {
      console.log(err)
      sendJson(res, 502, { error: 'store unavailable' })
    }
    return
  }

  sendJson(res, 404, { error: 'not found' })
})

server.listen(3000, () => console.log('listening on 3000'))
