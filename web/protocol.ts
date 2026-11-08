const CMD_SET = 1
const CMD_GET = 2
const CMD_DEL = 3

const STATUS_OK = 0
const STATUS_NOT_FOUND = 1

function lengthPrefix(n: number): Buffer {
  const buff = Buffer.alloc(4)

  buff.writeUInt32BE(n, 0)

  return buff
}

function encodeRequest(
  command: number,
  key: Buffer,
  value: Buffer = Buffer.alloc(0)
): Buffer {
  const comBuff = Buffer.from([command])
  const keyLenBuff = lengthPrefix(key.length)
  const payload = Buffer.concat([comBuff, keyLenBuff, key, value])

  return Buffer.concat([lengthPrefix(payload.length), payload])
}

function decodeResponse(payload: Buffer): {
  status: number
  body: Buffer
} {
  if (payload.length === 0) {
    throw new Error('response too short')
  }

  const status = payload[0]

  const body = payload.subarray(1)

  return { status, body }
}

export {
  CMD_DEL,
  CMD_GET,
  CMD_SET,
  STATUS_NOT_FOUND,
  STATUS_OK,
  lengthPrefix,
  encodeRequest,
  decodeResponse
}
