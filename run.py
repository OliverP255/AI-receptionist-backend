import threading
from main import run_flask
from websocket_server import run_websocket_server
from flask_app import run_flask_app

if __name__ == "__main__":
    # Remove this line to avoid blocking before threads start:
    # run_flask_app()
    
    # Start Flask in its own thread
    flask_thread = threading.Thread(target=run_flask_app)
    
    # Start WebSocket server in its own thread
    websocket_thread = threading.Thread(target=run_websocket_server)

    flask_thread.start()
    websocket_thread.start()

    flask_thread.join()
    websocket_thread.join()
