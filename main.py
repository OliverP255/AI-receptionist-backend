from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Flask server is running"

def run_flask():
    app.run(host="0.0.0.0", port=5050)
