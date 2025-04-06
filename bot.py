import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import threading
import pymongo
import feedparser
from config import API_ID, API_HASH, BOT_TOKEN, URL_A, START_PIC, MONGO_URI, ADMINS

from webhook import start_webhook
from modules.rss.rss import news_feed_loop

# MongoDB setup
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["AnimeNewsBot"]
user_settings_collection = db["user_settings"]
global_settings_collection = db["global_settings"]

# Pyrogram app
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start webhook in background
webhook_thread = threading.Thread(target=start_webhook, daemon=True)
webhook_thread.start()


async def escape_markdown_v2(text: str) -> str:
    return text


async def send_message_to_user(chat_id: int, message: str, image_url: str = None):
    try:
        if image_url:
            await app.send_photo(chat_id, image_url, caption=message)
        else:
            await app.send_message(chat_id, message)
    except Exception as e:
        print(f"Error sending message: {e}")


@app.on_message(filters.command("start"))
async def start(client, message):
    chat_id = message.chat.id
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴍᴀɪɴ ʜᴜʙ", url="https://t.me/Bots_Nation"),
            InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url="https://t.me/Bots_Nation_Support"),
        ],
        [
            InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴩᴇʀ", url="https://t.me/darkxside78"),
        ],
    ])

    await app.send_photo(
        chat_id,
        START_PIC,
        caption=(
            f"**ʙᴀᴋᴋᴀᴀᴀ {message.from_user.username}!!!**\n"
            f"**ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡs ʙᴏᴛ.**\n"
            f"**ɪ ᴛᴀᴋᴇ ᴀɴɪᴍᴇ ɴᴇᴡs ᴄᴏᴍɪɴɢ ғʀᴏᴍ ʀss ꜰᴇᴇᴅs ᴀɴᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴜᴘʟᴏᴀᴅ ɪᴛ ᴛᴏ ᴍʏ ᴍᴀsᴛᴇʀ's ᴀɴɪᴍᴇ ɴᴇᴡs ᴄʜᴀɴɴᴇʟ.**"
        ),
        reply_markup=buttons
    )


@app.on_message(filters.command("news"))
async def connect_news(client, message):
    chat_id = message.chat.id
    if message.from_user.id not in ADMINS:
        return await app.send_message(chat_id, "You do not have permission to use this command.")
    if len(message.text.split()) < 2:
        return await app.send_message(chat_id, "Please provide a channel username (without @).")

    channel = message.text.split()[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])

    if channel in channels:
        return await app.send_message(chat_id, f"@{channel} is already in the list.")

    channels.append(channel)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"news_channels": channels}}, upsert=True)
    await app.send_message(chat_id, f"Added @{channel} to the news channels list.")


@app.on_message(filters.command("listnews"))
async def list_news_channels(client, message):
    if message.from_user.id not in ADMINS:
        return await app.send_message(message.chat.id, "You don't have permission.")

    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])

    if not channels:
        return await app.send_message(message.chat.id, "No news channels added yet.")

    text = "**Configured News Channels:**\n\n" + "\n".join([f"- @{ch}" for ch in channels])
    await app.send_message(message.chat.id, text)


@app.on_message(filters.command("removenews"))
async def remove_news_channel(client, message):
    if message.from_user.id not in ADMINS:
        return await app.send_message(message.chat.id, "You don't have permission.")
    if len(message.text.split()) < 2:
        return await app.send_message(message.chat.id, "Please provide a channel to remove.")

    channel = message.text.split()[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])

    if channel not in channels:
        return await app.send_message(message.chat.id, f"@{channel} is not in the list.")

    channels.remove(channel)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"news_channels": channels}})
    await app.send_message(message.chat.id, f"Removed @{channel} from the list.")


async def main():
    await app.start()
    print("Bot is running...")

    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])
    asyncio.create_task(news_feed_loop(app, db, global_settings_collection, channels))

    await asyncio.Event().wait()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
