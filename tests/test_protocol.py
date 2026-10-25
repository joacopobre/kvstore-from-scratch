import socket

import pytest

from protocol import (
    recv_exact,
    decode_request, encode_request,
    decode_response, encode_response,
    frame,
    CMD_SET, CMD_GET, CMD_DEL,
    STATUS_OK, STATUS_NOT_FOUND, STATUS_ERROR,read_message, MAX_MESSAGE_SIZE
)


# ---------- recv_exact ----------

def test_recv_exact_reads_a_message_that_arrives_in_pieces():
    a, b = socket.socketpair()
    a.sendall(b"abc")
    a.sendall(b"de")
    assert recv_exact(b, 5) == b"abcde"
    a.close()
    b.close()


def test_recv_exact_reads_exactly_n_and_leaves_the_rest():
    a, b = socket.socketpair()
    a.sendall(b"abcdefgh")
    assert recv_exact(b, 5) == b"abcde"
    assert recv_exact(b, 3) == b"fgh"
    a.close()
    b.close()


def test_recv_exact_raises_if_the_connection_closes_early():
    a, b = socket.socketpair()
    a.sendall(b"abc")
    a.close()
    with pytest.raises(ConnectionError):
        recv_exact(b, 5)       # asks for 5, only 3 will ever arrive
    b.close()


# ---------- decode_request ----------

def test_decode_request_set():
    assert decode_request(b"\x01\x00\x00\x00\x03abcxyz") == (CMD_SET, b"abc", b"xyz")


def test_decode_request_get_has_empty_value():
    assert decode_request(b"\x02\x00\x00\x00\x01a") == (CMD_GET, b"a", b"")


def test_decode_request_too_short():
    with pytest.raises(ValueError, match="too short"):
        decode_request(b"\x01\x00\x00")


def test_decode_request_key_exceeds_payload():
    with pytest.raises(ValueError, match="exceeds"):
        decode_request(b"\x01\x00\x00\x00\x0a123")


def test_decode_request_unknown_command():
    with pytest.raises(ValueError, match="not recognized"):
        decode_request(b"\x05\x00\x00\x00\x01a")     # otherwise valid


# ---------- encode_request ----------

def test_encode_request_set():
    assert encode_request(CMD_SET, b"abc", b"xyz") == b"\x01\x00\x00\x00\x03abcxyz"


def test_encode_request_get():
    assert encode_request(CMD_GET, b"a") == b"\x02\x00\x00\x00\x01a"


def test_encode_request_set_hello():
    assert encode_request(CMD_SET, b"a", b"hello") == b"\x01\x00\x00\x00\x01ahello"


def test_request_round_trip():
    assert decode_request(encode_request(CMD_SET, b"k", b"v")) == (CMD_SET, b"k", b"v")


def test_request_is_binary_safe():
    key = b"a\x00b"                      # 3 bytes: 'a', a zero byte, 'b'
    payload = encode_request(CMD_SET, key, b"x")
    # worked out by hand: command, key length 3, the 3 key bytes, the value
    assert payload == b"\x01\x00\x00\x00\x03a\x00bx"
    assert decode_request(payload) == (CMD_SET, key, b"x")


def test_request_value_that_looks_like_a_request():
    fake = b"\x01\x00\x00\x00\x03abc"    # protocol-looking bytes inside the value
    payload = encode_request(CMD_SET, b"k", fake)
    assert decode_request(payload) == (CMD_SET, b"k", fake)


# ---------- frame ----------

def test_frame_adds_length_prefix():
    assert frame(b"abc") == b"\x00\x00\x00\x03abc"


def test_frame_of_empty_payload():
    assert frame(b"") == b"\x00\x00\x00\x00"


def test_set_request_on_the_wire():
    # 1 command + 4 key length + 1 key + 5 value = 11 bytes after the prefix
    assert frame(encode_request(CMD_SET, b"a", b"hello")) == (
        b"\x00\x00\x00\x0b" + b"\x01" + b"\x00\x00\x00\x01" + b"a" + b"hello"
    )


def test_get_request_on_the_wire():
    # 1 command + 4 key length + 1 key = 6 bytes after the prefix
    assert frame(encode_request(CMD_GET, b"a")) == (
        b"\x00\x00\x00\x06" + b"\x02" + b"\x00\x00\x00\x01" + b"a"
    )


# ---------- encode_response / decode_response ----------

def test_encode_response_with_body():
    assert encode_response(STATUS_OK, b"hello") == bytes([STATUS_OK]) + b"hello"


def test_encode_response_without_body():
    assert encode_response(STATUS_NOT_FOUND) == bytes([STATUS_NOT_FOUND])


def test_decode_response_with_body():
    assert decode_response(bytes([STATUS_OK]) + b"hello") == (STATUS_OK, b"hello")


def test_decode_response_without_body():
    assert decode_response(bytes([STATUS_NOT_FOUND])) == (STATUS_NOT_FOUND, b"")


def test_response_round_trip():
    assert decode_response(encode_response(STATUS_OK, b"v")) == (STATUS_OK, b"v")


def test_response_body_is_binary_safe():
    body = b"a\x00b\n"
    assert decode_response(encode_response(STATUS_OK, body)) == (STATUS_OK, body)


def test_decode_response_empty_payload():
    with pytest.raises(ValueError, match="Empty payload"):         
        decode_response(b"")                 # there is no status byte


def test_decode_response_unknown_status():
    with pytest.raises(ValueError, match="unrecognized status code"):         
        decode_response(b"\x09abc")          # 9 is not a status you defined


def test_found_response_on_the_wire():
    # 1 status byte + 5 body bytes = 6 bytes after the prefix
    assert frame(encode_response(STATUS_OK, b"hello")) == (
        b"\x00\x00\x00\x06" + bytes([STATUS_OK]) + b"hello"
    )


def test_not_found_response_on_the_wire():
    # 1 status byte, no body
    assert frame(encode_response(STATUS_NOT_FOUND)) == (
        b"\x00\x00\x00\x01" + bytes([STATUS_NOT_FOUND])
    )

def test_read_message_returns_the_payload():
    a, b = socket.socketpair()
    a.sendall(frame(b"abc"))
    # TODO: assert read_message(b) == b"abc"
    a.close()
    b.close()


def test_read_message_two_messages_back_to_back():
    a, b = socket.socketpair()
    a.sendall(frame(b"abc") + frame(b"defgh"))      # both frames arrive together
    # TODO: assert the first read_message(b) gives b"abc" and the second gives b"defgh"
    a.close()
    b.close()


def test_read_message_empty_payload():
    a, b = socket.socketpair()
    a.sendall(frame(b""))
    # TODO: assert read_message(b) == b""
    a.close()
    b.close()


def test_read_message_connection_closed_mid_message():
    a, b = socket.socketpair()
    a.sendall(b"\x00\x00\x00\x05ab")                # promises 5 bytes, delivers 2
    a.close()
    with pytest.raises(ConnectionError):
        read_message(b)
    b.close()


def test_read_message_rejects_oversized_length():
    a, b = socket.socketpair()
    a.sendall((MAX_MESSAGE_SIZE + 1).to_bytes(4, "big"))     # only the prefix; no body
    with pytest.raises(ValueError, match=f"message size too big, max message size is {MAX_MESSAGE_SIZE} MB"):
        read_message(b)
    a.close()
    b.close()