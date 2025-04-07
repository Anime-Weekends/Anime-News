from flask import Flask, request
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, WEBHOOK_URL

app = Flask(__name__)
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        bot.process_update(update)
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

if __name__ == "__main__":
    bot.start()
    app.run(host="0.0.0.0", port=8080)
