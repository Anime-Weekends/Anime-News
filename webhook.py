from flask import Flask, request
import asyncio
from config import BOT_TOKEN

# Initialize Flask app
flask_app = Flask(__name__)

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def process_update():
        from bot import app as pyrogram_app
        await pyrogram_app.process_update(update)

    loop.run_until_complete(process_update())
    return "OK", 200

def start_webhook():
    flask_app.run(host="0.0.0.0", port=8080)
