import http from 'node:http'
import { KVClient } from '../client'
import fs from 'node:fs/promises'
import path from 'node:path'

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

  if (req.method === 'POST' && url.pathname === '/api/set') {
    const data = await readJson(req, res)
    if (data === null) return
    const key = data.key
    const value = data.value
    if (typeof key !== 'string' || key === '') {
      sendJson(res, 400, { error: 'key must be a non-empty string' })
      return
    }
    if (typeof value !== 'string') {
      sendJson(res, 400, { error: 'value must be a string' })
      return
    }
    await withClient(res, async (client) => {
      await client.set(Buffer.from(key), Buffer.from(value))
      sendJson(res, 200, { ok: true })
    })
    return
  }

  if (req.method === 'POST' && url.pathname === '/api/delete') {
    const data = await readJson(req, res)
    if (data === null) return
    const key = data.key
    if (typeof key !== 'string' || key === '') {
      sendJson(res, 400, { error: 'key must be a non-empty string' })
      return
    }
    await withClient(res, async (client) => {
      await client.delete(Buffer.from(key))
      sendJson(res, 200, { ok: true })
    })
    return
  }

  if (req.method === 'GET' && url.pathname === '/api/get') {
    const key = url.searchParams.get('key')
    if (!key) {
      sendJson(res, 400, { error: 'missing key' })
      return
    }

    await withClient(res, async (client) => {
      const value = await client.get(Buffer.from(key))
      if (value === null) {
        sendJson(res, 404, { error: 'not found' })
      } else {
        sendJson(res, 200, { value: value.toString() })
      }
    })
    return
  }
  if (req.method === 'GET' && (await serveStatic(res, url.pathname))) return

  sendJson(res, 404, { error: 'not found' })
})

async function withClient(
  res: http.ServerResponse,
  action: (client: KVClient) => Promise<void>
): Promise<void> {
  try {
    const client = await KVClient.connect(STORE_HOST, STORE_PORT)
    try {
      await action(client)
    } finally {
      client.close()
    }
  } catch (err) {
    console.log(err)
    sendJson(res, 502, { error: 'store unavailable' })
  }
}

async function readJson(
  req: http.IncomingMessage,
  res: http.ServerResponse
): Promise<Record<string, unknown> | null> {
  let body: Buffer
  try {
    body = await readBody(req)
  } catch {
    sendJson(res, 413, { error: 'body too large' })
    return null
  }
  let data
  try {
    data = JSON.parse(body.toString())
  } catch {
    sendJson(res, 400, { error: 'invalid JSON' })
    return null
  }
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    sendJson(res, 400, { error: 'body must be a JSON object' })
    return null
  }
  return data
}

const DIST = path.resolve('dist') // run the app from inside web/
const TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.json': 'application/json'
}

async function serveStatic(
  res: http.ServerResponse,
  pathname: string
): Promise<boolean> {
  if (pathname === '/') {
    pathname = '/index.html'
  }
  const fullPath = path.join(DIST, pathname)
  if (!path.resolve(fullPath).startsWith(DIST + path.sep)) {
    return false
  }
  // TODO 3: read the file with fs.readFile; if that fails (no such file), return false
  let buff
  try {
    buff = await fs.readFile(fullPath)
  } catch {
    return false
  }
  // TODO 4: set Content-Type from the file's extension (path.extname + TYPES),
  //   send the file's bytes, and return true
  res.setHeader(
    'Content-Type',
    TYPES[path.extname(fullPath)] ?? 'application/octet-stream'
  )
  res.end(buff)
  return true
}

server.listen(3000, () => console.log('listening on 3000'))
