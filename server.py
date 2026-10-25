from protocol import encode_response, STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK, CMD_DEL, CMD_GET, CMD_SET

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