# webhook.py

from flask import Flask, request
from bot import app as pyro_app
from config import WEBHOOK_URL, BOT_TOKEN

app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_data()
    pyro_app.process_webhook_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def root():
    return "Bot is alive!", 200

if __name__ == "__main__":
    pyro_app.set_webhook(WEBHOOK_URL + f"/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=8080)
