import pytest

from engine import Store
from protocol import (
    CMD_SET, CMD_GET, CMD_DEL,
    STATUS_OK, STATUS_NOT_FOUND,
    encode_response,
)
from server import handle_request


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