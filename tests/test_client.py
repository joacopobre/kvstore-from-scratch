import threading

import pytest

from client import KVClient, ServerError
from engine import Store
from protocol import STATUS_ERROR, encode_response, frame, read_message
from server import accept_loop, create_listener


# ---------- helpers ----------

def start_server(tmp_path):
    """A real store served over TCP on a free port, running in a daemon thread."""
    store = Store(str(tmp_path))
    listener = create_listener("127.0.0.1", 0)
    port = listener.getsockname()[1]
    threading.Thread(target=accept_loop, args=(listener, store), daemon=True).start()
    return port, listener


def with_client(tmp_path):
    port, listener = start_server(tmp_path)
    return KVClient("127.0.0.1", port), listener


def start_fake_error_server():
    """A fake server that answers the first request with STATUS_ERROR and the body b"boom"."""
    listener = create_listener("127.0.0.1", 0)
    port = listener.getsockname()[1]

    def fake():
        conn, _ = listener.accept()
        read_message(conn)                                   # swallow the request
        conn.sendall(frame(encode_response(STATUS_ERROR, b"boom")))
        conn.close()

    threading.Thread(target=fake, daemon=True).start()
    return port, listener


# ---------- behaviour against a real server ----------

def test_client_set_then_get(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        client.set(b"a", b"hello")
        assert client.get(b"a") == b"hello"
    finally:
        client.close()
        listener.close()


def test_get_missing_key_returns_none(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        assert client.get(b"nope") is None
    finally:
        client.close()
        listener.close()


def test_delete_then_get_returns_none(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        client.set(b"a", b"hello")
        client.delete(b"a")
        assert client.get(b"a") is None
    finally:
        client.close()
        listener.close()


def test_delete_missing_key_does_not_raise(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        client.delete(b"never-set")          # deleting a key that isn't there is fine
        assert client.get(b"never-set") is None
    finally:
        client.close()
        listener.close()


def test_empty_value_is_not_none(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        client.set(b"k", b"")
        value = client.get(b"k")
        assert value == b""
        assert value is not None             # an empty value is a real value, not "missing"
    finally:
        client.close()
        listener.close()


def test_overwrite_returns_newest_value(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        client.set(b"k", b"first")
        client.set(b"k", b"second")
        assert client.get(b"k") == b"second"
    finally:
        client.close()
        listener.close()


def test_binary_safe_key_and_value(tmp_path):
    client, listener = with_client(tmp_path)
    try:
        key = b"a\x00b"
        value = b"x\ny\x00z"
        client.set(key, value)
        assert client.get(key) == value
    finally:
        client.close()
        listener.close()


def test_two_clients_share_the_same_store(tmp_path):
    port, listener = start_server(tmp_path)
    first = KVClient("127.0.0.1", port)
    second = KVClient("127.0.0.1", port)
    try:
        first.set(b"shared", b"yes")
        assert second.get(b"shared") == b"yes"      # the first client's SET has been answered,
        second.set(b"other", b"too")                 # so the second client can rely on it
        assert first.get(b"other") == b"too"
    finally:
        first.close()
        second.close()
        listener.close()


# ---------- error handling against a fake server ----------

@pytest.mark.parametrize("operation", [
    lambda client: client.set(b"a", b"b"),
    lambda client: client.get(b"a"),
    lambda client: client.delete(b"a"),
])
def test_client_raises_server_error(operation):
    port, listener = start_fake_error_server()
    client = KVClient("127.0.0.1", port)
    try:
        with pytest.raises(ServerError, match="boom"):
            operation(client)
    finally:
        client.close()
        listener.close()