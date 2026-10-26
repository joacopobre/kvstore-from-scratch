
import socket

from protocol import CMD_DEL, CMD_GET, CMD_SET, decode_response, encode_request, frame, read_message, STATUS_OK, STATUS_NOT_FOUND, STATUS_ERROR
           # the functions and constants you need


class ServerError(Exception):
    pass

class KVClient:
    def __init__(self, host, port):
        self._sock = socket.create_connection((host, port))
        self._sock.settimeout(5)
        

    def _request(self, command, key, value=b""):
        self._sock.sendall(frame(encode_request(command, key, value)))   # send one request
        return decode_response(read_message(self._sock))                 

    def set(self, key, value):
        status, body = self._request(CMD_SET, key, value)
        if status == STATUS_OK:
            return 
        else:
            raise ServerError(body.decode())


    def get(self, key):
        status, body = self._request(CMD_GET, key)
        if status == STATUS_OK:
            return body
        elif status == STATUS_NOT_FOUND:
            return None
        else:
            raise ServerError(body.decode())

    def delete(self, key):
        status, body = self._request(CMD_DEL, key)
        if status == STATUS_OK:
            return 
        else:
            raise ServerError(body.decode())

    def close(self):
        self._sock.close()
