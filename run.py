import threading
from websocket_server import run_websocket_server

if __name__ == "__main__":
    # Just run the WebSocket server (no Flask anymore)
    websocket_thread = threading.Thread(target=run_websocket_server)

    websocket_thread.start()
    websocket_thread.join()
