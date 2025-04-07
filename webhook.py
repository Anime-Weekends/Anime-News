from flask import Flask, request
from pyrogram import Client
from config import BOT_TOKEN, WEBHOOK_URL, API_ID, API_HASH

app = Flask(__name__)

bot = Client(
    "AnimeNewsBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_data()
    bot.process_update(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running with webhook", 200

if __name__ == "__main__":
    bot.start()
    bot.set_webhook(WEBHOOK_URL + f"/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=8080)
