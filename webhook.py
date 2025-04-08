# webhook.py

from flask import Flask, request
from config import BOT_TOKEN
from bot import app  # Make sure bot.py defines "app" as your Pyrofork client

web = Flask(__name__)

@web.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if update:
        app.receive_update(update)
    return "OK", 200

if __name__ == "__main__":
    web.run(host="0.0.0.0", port=8000)
