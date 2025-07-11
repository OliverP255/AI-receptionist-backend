from flask import Flask
import os

PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)

@app.route("/")
def index():
    return "Flask server is running"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

