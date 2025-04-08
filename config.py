import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
START_PIC = os.getenv("START_PIC")
URL_A = os.getenv("URL_A")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS = list(map(int, os.getenv("ADMINS", str(OWNER_ID)).split(",")))
