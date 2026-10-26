from protocol import encode_response, STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK, CMD_DEL, CMD_GET, CMD_SET, read_message, decode_response, frame, decode_request
import socket
import threading
def handle_request(store, command, key, value =b""):
    if command == CMD_SET:
        store.set(key, value)
        return encode_response(STATUS_OK)
    elif command == CMD_DEL:
        store.delete(key) # if the key is there or not we dont care, we care that the key is not in at the end.
        return encode_response(STATUS_OK)
    elif command == CMD_GET:
        result = store.get(key)
        if result is None:
            return encode_response(STATUS_NOT_FOUND)
        return encode_response(STATUS_OK, result)
    else:
        raise ValueError("unrecognized command value")

def serve_connection(conn, store):
    try:
        while True:
            payload = read_message(conn)
            try:
                command, key, value = decode_request(payload)
                response = handle_request(store, command, key, value)
            except ValueError as e:
                response = encode_response(STATUS_ERROR, str(e).encode())
            except Exception as e:
                print(f"internal error: {e!r}")
                response = encode_response(STATUS_ERROR, b"internal error")
            conn.sendall(frame(response))
    except ConnectionError:
        pass
    except ValueError as e:
        response = encode_response(STATUS_ERROR, str(e).encode())
        try:
            conn.sendall(frame(response))
        except ConnectionError:
            pass
    finally:
        conn.close()


def create_listener(host="127.0.0.1", port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # IPv4, TCP
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # lets you restart quickly
    server.bind((host, port))
    server.listen()
    return server 

def accept_loop(listener, store):
    while True:
        conn, addr = listener.accept()
        thread = threading.Thread(target=serve_connection, args=(conn, store), daemon=True)
        thread.start()

