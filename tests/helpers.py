import threading

from engine import Store
from server import accept_loop, create_listener


def start_server(tmp_path):
    """Helper: a store, a listener on a free port, and accept_loop running in a daemon thread."""
    store = Store(str(tmp_path))
    listener = create_listener("127.0.0.1", 0)
    port = listener.getsockname()[1]
    threading.Thread(target=accept_loop, args=(listener, store), daemon=True).start()
    return port, listener