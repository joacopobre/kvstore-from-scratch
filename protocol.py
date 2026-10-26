
import socket


COMMAND_LEN = 1 
KEY_LENGTH = 4
LENGTH_PREFIX_SIZE = 4
STATUS_LENGTH = 1

CMD_SET = 1
CMD_GET = 2
CMD_DEL = 3 

STATUS_OK = 0
STATUS_NOT_FOUND = 1
STATUS_ERROR = 2

MAX_MESSAGE_SIZE = 16 * 1024 * 1024    # 16 MB in bytes

def recv_exact(sock, n):
    buffer = b''
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if chunk == b'':
            raise ConnectionError("connection closed before all bytes arrived")
        buffer += chunk
    return buffer

def decode_request(payload: bytes)-> tuple[int, bytes, bytes]:
    header_size = COMMAND_LEN + KEY_LENGTH

    if len(payload) < header_size:
        raise ValueError("request too short to containd a command and a key length")
    
    command_bytes = payload[0:COMMAND_LEN]
    command = int.from_bytes(command_bytes, 'big')

    if command not in (CMD_DEL, CMD_GET, CMD_SET):
        raise ValueError("command not recognized")
    
    key_len_bytes = payload[COMMAND_LEN : header_size]
    key_len = int.from_bytes(key_len_bytes, 'big')

    if header_size + key_len > len(payload):
        raise ValueError("length of the key exceeds the payload bounds")

    key_end = header_size + key_len 
    key_bytes = payload[header_size : key_end]
    value_bytes = payload[key_end :]

    return command , key_bytes, value_bytes

def encode_request(command: int, key: bytes, value: bytes = b'') -> bytes:
    command_bytes = command.to_bytes(COMMAND_LEN, 'big')
    key_len_bytes = len(key).to_bytes(KEY_LENGTH, 'big')

    return command_bytes + key_len_bytes + key + value

def frame(payload: bytes) -> bytes:
    length = len(payload).to_bytes(LENGTH_PREFIX_SIZE, 'big')
    return length + payload

def encode_response(status: int, body: bytes =b"") -> bytes:
    status_bytes = status.to_bytes(STATUS_LENGTH, 'big')

    return status_bytes + body

def decode_response(payload: bytes) -> tuple[int, bytes]:
    if len(payload) < 1:
        raise ValueError("Empty payload")
    status_bytes = payload[0:STATUS_LENGTH]
    status = int.from_bytes(status_bytes, 'big')

    if status not in (STATUS_ERROR, STATUS_OK, STATUS_NOT_FOUND):
        raise ValueError("unrecognized status code")
    body = payload[STATUS_LENGTH:]

    return status, body

def read_message(sock: socket.socket) -> bytes:
    length_bytes = recv_exact(sock, LENGTH_PREFIX_SIZE)
    length = int.from_bytes(length_bytes, 'big')

    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"message size too big, max message size is {MAX_MESSAGE_SIZE} MB")
    
    message = recv_exact(sock, length)
    return message
