
function lengthPrefix(n: number): Buffer {
  const buff = Buffer.alloc(4)

  buff.writeUInt32BE(n, 0)

  return buff
}



export function encodeRequest(
  command: number,
  key: Buffer,
  value: Buffer = Buffer.alloc(0)
): Buffer {
  const comBuff = Buffer.from([command])
  const keyLenBuff = lengthPrefix(key.length)
  const payload = Buffer.concat([comBuff, keyLenBuff, key, value])

  return Buffer.concat([lengthPrefix(payload.length), payload])
}



export function decodeResponse(payload: Buffer): { status: number; body: Buffer } {
  if (payload.length === 0) {
    throw new Error('response too short')
  }

  const status = payload[0]

  const body = payload.subarray(1)

  return { status, body }
}




