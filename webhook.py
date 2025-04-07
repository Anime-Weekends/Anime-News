from flask import Flask, request
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, WEBHOOK_URL
import threading
import asyncio

app = Flask(__name__)
bot = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        bot.process_update(request.get_data())
        return "", 200
    return "Invalid request", 400

def start_webhook():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.set_webhook(WEBHOOK_URL + f"/{BOT_TOKEN}"))
        print("Webhook set to:", WEBHOOK_URL)
        app.run(host="0.0.0.0", port=8080)

    threading.Thread(target=run).start()
