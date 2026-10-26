import pytest
import socket
import threading
from engine import Store
from protocol import (
    CMD_SET, CMD_GET, CMD_DEL,
    STATUS_OK, STATUS_NOT_FOUND, STATUS_ERROR, 
    encode_response,decode_response,frame,encode_request,read_message, MAX_MESSAGE_SIZE
)
from server import handle_request, serve_connection





def make_store(tmp_path):
    return Store(str(tmp_path))


def test_set_returns_ok_with_no_body(tmp_path):
    store = make_store(tmp_path)
    assert handle_request(store, CMD_SET, b"a", b"hello") == encode_response(STATUS_OK)
   

def test_set_then_get(tmp_path):
    store = make_store(tmp_path)
    handle_request(store, CMD_SET, b"a", b"hello")
    assert handle_request(store, CMD_GET, b"a") == encode_response(STATUS_OK, b"hello")
    


def test_get_missing_key(tmp_path):
    store = make_store(tmp_path)
    assert handle_request(store, CMD_GET, b"nope") == encode_response(STATUS_NOT_FOUND)
    

def test_delete_then_get(tmp_path):
    store = make_store(tmp_path)
    handle_request(store, CMD_SET, b"a", b"hello")
    assert handle_request(store, CMD_DEL, b"a") == encode_response(STATUS_OK)
    assert handle_request(store, CMD_GET, b"a") == encode_response(STATUS_NOT_FOUND)
    


def test_delete_missing_key_is_still_ok(tmp_path):
    store = make_store(tmp_path)
    
    assert handle_request(store, CMD_DEL, b"a") == encode_response(STATUS_OK)


def test_get_empty_value_is_ok_not_not_found(tmp_path):
    store = make_store(tmp_path)
    handle_request(store, CMD_SET, b"a", b"")
    assert handle_request(store, CMD_GET, b"a") == encode_response(STATUS_OK, b"")
    


def test_overwrite_returns_latest_value(tmp_path):
    store = make_store(tmp_path)
    handle_request(store, CMD_SET, b"a", b"1")
    handle_request(store, CMD_SET, b"a", b"2")
    # TODO: assert the GET response contains b"2"
    assert handle_request(store, CMD_GET, b"a") == encode_response(STATUS_OK, b"2")


def test_unknown_command_raises(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="unrecognized command value"):
        handle_request(store, 99, b"a", b"")

def test_serve_connection_set_then_get(tmp_path):
    store = Store(str(tmp_path))
    client, server_side = socket.socketpair()
    client.settimeout(2)          # a broken server fails the test after 2s, not hangs forever

    thread = threading.Thread(target=serve_connection, args=(server_side, store))
    thread.start()

    client.sendall(frame(encode_request(CMD_SET, b"a", b"hello")))
    status, body = decode_response(read_message(client))
    assert status == STATUS_OK

    client.sendall(frame(encode_request(CMD_GET, b"a")))
    status, body = decode_response(read_message(client))
    assert (status, body) == (STATUS_OK, b"hello")

    client.close()                # the client leaves
    thread.join(timeout=2)
    assert not thread.is_alive()  # so the server loop must have ended

def start_serving(tmp_path):
    """Helper: a store, a socket pair and a running serve_connection thread."""
    store = Store(str(tmp_path))
    client, server_side = socket.socketpair()
    client.settimeout(2)
    thread = threading.Thread(target=serve_connection, args=(server_side, store))
    thread.start()
    return store, client, thread


def test_serve_connection_ends_when_client_disconnects(tmp_path):
    store, client, thread = start_serving(tmp_path)
    client.close()
    thread.join(timeout=2)
    assert not thread.is_alive()


def test_serve_connection_malformed_request_gets_error_and_connection_survives(tmp_path):
    store, client, thread = start_serving(tmp_path)

    client.sendall(frame(b"\x05"))                       # a valid frame with a garbage payload
    
    status, body = decode_response(read_message(client))
    assert status == STATUS_ERROR

    # the same connection must still work
    client.sendall(frame(encode_request(CMD_SET, b"a", b"hello")))
    
    status, body = decode_response(read_message(client))
    assert status == STATUS_OK
    client.sendall(frame(encode_request(CMD_GET, b"a")))
    
    status, body = decode_response(read_message(client))
    assert status == STATUS_OK
    assert body == b"hello"

    client.close()
    thread.join(timeout=2)


def test_serve_connection_unknown_command_gets_error(tmp_path):
    store, client, thread = start_serving(tmp_path)

    client.sendall(frame(b"\x09\x00\x00\x00\x01a"))      # command 9, otherwise a valid request
    
    status, body = decode_response(read_message(client))
    assert status == STATUS_ERROR

    client.close()
    thread.join(timeout=2)


def test_serve_connection_oversized_length_gets_error_then_closes(tmp_path):
    store, client, thread = start_serving(tmp_path)

    client.sendall((MAX_MESSAGE_SIZE + 1).to_bytes(4, "big"))   # only the prefix, no body
    # TODO: read one response and assert STATUS_ERROR
    status, body = decode_response(read_message(client))
    assert status == STATUS_ERROR
    with pytest.raises(ConnectionError):
        read_message(client)                             # the server closed the connection

    thread.join(timeout=2)
    
    assert not thread.is_alive()

def test_serve_connection_delete_then_get_not_found(tmp_path):
    store, client, thread = start_serving(tmp_path)
    # TODO: SET a key, DEL it, GET it, and assert the last status is STATUS_NOT_FOUND
    client.sendall(frame(encode_request(CMD_SET, b"a", b"HELLO")))
    status, _ = decode_response(read_message(client))
    assert status == STATUS_OK

    client.sendall(frame(encode_request(CMD_DEL, b"a")))
    status, _ = decode_response(read_message(client))
    assert status == STATUS_OK

    client.sendall(frame(encode_request(CMD_GET, b"a")))
    status, _ = decode_response(read_message(client))
    assert status == STATUS_NOT_FOUND
    client.close()
    thread.join(timeout=2)