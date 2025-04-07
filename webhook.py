from flask import Flask, request
from bot import app  # This should be the Pyrofork Client

server = Flask(__name__)

@server.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        app.process_update(request.get_json(force=True))
        return "OK", 200
    return "Running", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
