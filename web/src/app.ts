import http from 'node:http'
import { KVClient } from '../client'
import { send } from 'node:process'
import { buffer } from 'node:stream/consumers'

const STORE_HOST = '127.0.0.1'
const STORE_PORT = 9000

function sendJson(
  res: http.ServerResponse,
  status: number,
  body: unknown
): void {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(body))
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', 'http://localhost')

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
