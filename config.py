# config.py

import os

API_ID = int(os.getenv("API_ID", "28744454"))
API_HASH = os.getenv("API_HASH", "debd37cef0ad1a1ce45d0be8e8c3c5e7")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-bot-token")
MONGO_URI = os.getenv("MONGO_URI", "your-mongo-uri")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-webhook-url.koyeb.app")

START_PIC = os.getenv("START_PIC", "https://i.ibb.co/ynjcqYdZ/photo-2025-04-06-20-48-47-7490304985767346192.jpg")

OWNER_ID = int(os.getenv("OWNER_ID", "6266529037"))
ADMINS = list(map(int, os.getenv("ADMINS", "6266529037").split(",")))

URL_A = "https://myanimelist.net/rss.php?type=news"
