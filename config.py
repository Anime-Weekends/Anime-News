import os

API_ID = int(os.environ.get("API_ID"))  # set API_ID=28744454 in your environment
API_HASH = os.environ.get("API_HASH")  # set API_HASH=debd37cef0ad1a1ce45d0be8e8c3c5e7 in your environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # set BOT_TOKEN=7773900178:AAEQEQAXahfYAVsol1EUcwYPKa0Or2cPCdg in your environment
URL_A = os.environ.get("URL_A", "http://myanimelist.net/rss.php?type=news")
START_PIC = os.environ.get("START_PIC", "https://i.ibb.co/ynjcqYdZ/photo-2025-04-06-20-48-47-7490304985767346192.jpg")
MONGO_URI = os.environ.get("MONGO_URI")  # set MONGO_URI to your MongoDB connection string in your environment
OWNER_ID = int(os.environ.get("OWNER_ID", 6266529037))

#By RexySama
