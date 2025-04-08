from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify("Auto Anime News Bot is running!")

@app.route("/health")
def health():
    return jsonify({"status": "OK"})

def start_webhook():
    app.run(host="0.0.0.0", port=8000, threaded=True)
