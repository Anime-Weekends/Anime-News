import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("28744454"))
API_HASH = os.getenv("debd37cef0ad1a1ce45d0be8e8c3c5e7")
BOT_TOKEN = os.getenv("7773900178:AAEQEQAXahfYAVsol1EUcwYPKa0Or2cPCdg")
WEBHOOK_URL = os.getenv("")
START_PIC = os.getenv("https://i.ibb.co/ynjcqYdZ/photo-2025-04-06-20-48-47-7490304985767346192.jpg")
URL_A = os.getenv("https://myanimelist.net/rss.php?type=news")
MONGO_URI = os.getenv("")
OWNER_ID = int(os.getenv("6266529037"))
ADMINS = list(map(int, os.getenv("ADMINS", "6266529037").split(",")))
