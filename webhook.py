# webhook.py

from flask import Flask, request
from pyrogram import Client
from config import BOT_TOKEN, URL_A

app_webhook = Flask(__name__)
client: Client = None  # Will be assigned externally by bot.py

@app_webhook.route('/')
def index():
    return 'AnimeNewsBot is running with webhook!', 200

@app_webhook.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    if request.headers.get("content-type") == "application/json":
        update = request.get_data().decode("utf-8")
        client.process_update(update)
        return "OK", 200
    return "Invalid content type", 400

def start_webhook():
    import os
    from pyrogram import Client
    import logging

    logging.basicConfig(level=logging.INFO)

    global client
    client = Client(
        "AnimeNewsBot",
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        bot_token=BOT_TOKEN
    )

    # Set webhook
    import asyncio
    asyncio.run(client.set_webhook(URL_A + BOT_TOKEN))

    # Start Flask server (Koyeb exposes port 8080)
    app_webhook.run(host="0.0.0.0", port=8080)
