from flask import Flask, request, jsonify
import asyncio

app = Flask(__name__)

@app.route("/")
def root_route_handler():
    return jsonify("RexySama - The darkness shall follow my command")

@app.route("/health")
def health_check():
    return jsonify({"status": "OK"})

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_data()
    asyncio.create_task(pyro_app.process_webhook_update(update))  # "pyro_app" must be your Pyrogram Client instance
    return "OK"

def start_webhook():
    app.run(host="0.0.0.0", port=8000, threaded=True)
