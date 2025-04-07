import aiohttp
import asyncio
import threading
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import pymongo

from config import API_ID, API_HASH, BOT_TOKEN, URL_A, START_PIC, MONGO_URI, ADMINS
from webhook import start_webhook
from modules.rss.rss import fetch_and_send_news

# MongoDB setup
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["AnimeNewsBot"]
user_settings_collection = db["user_settings"]
global_settings_collection = db["global_settings"]
admins_col = db["admins"]

# Pyrogram app
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start webhook server in background
webhook_thread = threading.Thread(target=start_webhook, daemon=True)
webhook_thread.start()

# Admin checker
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS or admins_col.find_one({"user_id": user_id}) is not None

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user else "User"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Mᴀɪɴ ʜᴜʙ", url="https://t.me/RexySama"),
         InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url="https://t.me/RexySama")],
        [InlineKeyboardButton("Dᴇᴠᴇʟᴏᴩᴇʀ", url="https://t.me/RexySama")]
    ])
    await client.send_photo(
        chat_id,
        START_PIC,
        caption=(
            f"**<blockquote>ʙᴀᴋᴋᴀᴀᴀ {username} !!!</blockquote>**\n"
            f"**ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡs ʙᴏᴛ.**\n"
            f"**ɪ ᴛᴀᴋᴇ ᴀɴɪᴍᴇ ɴᴇᴡs ᴄᴏᴍɪɴɢ ғʀᴏᴍ ʀss ꜰᴇᴇᴅs ᴀɴᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴜᴘʟᴏᴀᴅ ɪᴛ ᴛᴏ ᴍʏ ᴍᴀsᴛᴇʀ's ᴀɴɪᴍᴇ ɴᴇᴡs ᴄʜᴀɴɴᴇʟ.**"
        ),
        reply_markup=buttons
    )

# === News Channel Commands ===

@app.on_message(filters.command("news"))
async def connect_news(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You do not have permission.")
    if len(message.command) < 2:
        return await message.reply("Please provide a channel username (without @).")
    channel = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])
    if channel in channels:
        return await message.reply(f"@{channel} is already added.")
    channels.append(channel)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"news_channels": channels}}, upsert=True)
    await message.reply(f"Added @{channel} to the news channels.")

@app.on_message(filters.command("listnews"))
async def list_news_channels(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You don't have permission.")
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])
    if not channels:
        return await message.reply("No news channels added yet.")
    await message.reply("**Configured News Channels:**\n\n" + "\n".join(f"- @{ch}" for ch in channels))

@app.on_message(filters.command("removenews"))
async def remove_news_channel(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You don't have permission.")
    if len(message.command) < 2:
        return await message.reply("Provide the channel to remove.")
    channel = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])
    if channel not in channels:
        return await message.reply("Channel not found in list.")
    channels.remove(channel)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"news_channels": channels}})
    await message.reply(f"Removed @{channel} from news channels.")

# === RSS Feed Commands ===

@app.on_message(filters.command("addrss") & filters.private)
async def add_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addrss <rss_url>")
    url = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if url in feeds:
        return await message.reply("RSS already exists.")
    feeds.append(url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}}, upsert=True)
    await message.reply("RSS feed added.")

@app.on_message(filters.command("removerss") & filters.private)
async def remove_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removerss <rss_url>")
    url = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if url not in feeds:
        return await message.reply("Feed not found.")
    feeds.remove(url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}})
    await message.reply("RSS feed removed.")

@app.on_message(filters.command("listrss") & filters.private)
async def list_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if not feeds:
        return await message.reply("No RSS feeds found.")
    await message.reply("**RSS Feeds:**\n\n" + "\n".join(f"- {url}" for url in feeds))

# === Admin Commands ===

@app.on_message(filters.command("addadmin") & filters.private)
async def add_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addadmin <user_id>")
    try:
        user_id = int(message.command[1])
        if is_admin(user_id):
            return await message.reply("Already an admin.")
        admins_col.insert_one({"user_id": user_id})
        await message.reply(f"User {user_id} added as admin.")
    except ValueError:
        await message.reply("Invalid ID.")

@app.on_message(filters.command("removeadmin") & filters.private)
async def remove_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removeadmin <user_id>")
    try:
        user_id = int(message.command[1])
        if user_id in ADMINS:
            return await message.reply("Cannot remove static admin.")
        result = admins_col.delete_one({"user_id": user_id})
        if result.deleted_count:
            await message.reply("Admin removed.")
        else:
            await message.reply("Not a dynamic admin.")
    except ValueError:
        await message.reply("Invalid ID.")

@app.on_message(filters.command("listadmins") & filters.private)
async def list_admins(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    static_admins = [str(uid) for uid in ADMINS]
    dynamic_admins = [str(admin["user_id"]) for admin in admins_col.find()]
    await message.reply("**Admins:**\n" + "\n".join(static_admins + dynamic_admins))

# === Bot Startup ===

async def main():
    await app.start()
    await app.set_webhook(f"{URL_A}/{BOT_TOKEN}")
    print("Bot started with webhook.")

    try:
        await app.send_message(ADMINS[0], "<b>✅ Bot started successfully.</b>")
    except Exception as e:
        print(f"Failed to send startup message: {e}")

    async def periodic_news_loop():
        while True:
            await fetch_and_send_news(app, db, global_settings_collection)
            await asyncio.sleep(600)

    asyncio.create_task(periodic_news_loop())
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
