import aiohttp
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import threading
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
            InlineKeyboardButton("Mᴀɪɴ ʜᴜʙ", url="https://t.me/RexySama"),
            InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url="https://t.me/RexySama"),
        ],
        [
            InlineKeyboardButton("Dᴇᴠᴇʟᴏᴩᴇʀ", url="https://t.me/RexySama"),
        ],
    ])
    username = message.from_user.username if message.from_user and message.from_user.username else "User"
    await app.send_photo(
        chat_id,
        START_PIC,
        caption=(
            f"**<blockquote>ʙᴀᴋᴋᴀᴀᴀ {username} !!!</blockquote>**\n"
            f"**ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡs ʙᴏᴛ.**\n"
            f"**ɪ ᴛᴀᴋᴇ ᴀɴɪᴍᴇ ɴᴇᴡs ᴄᴏᴍɪɴɢ ғʀᴏᴍ ʀss ꜰᴇᴇᴅs ᴀɴᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴜᴘʟᴏᴀᴅ ɪᴛ ᴛᴏ ᴍʏ ᴍᴀsᴛᴇʀ's ᴀɴɪᴍᴇ ɴᴇᴡs ᴄʜᴀɴɴᴇʟ.**"
        ),
        reply_markup=buttons
    )

def is_admin(user_id: int) -> bool:
    if user_id in ADMINS:
        return True
    return admins_col.find_one({"user_id": user_id}) is not None

# NEWS CHANNEL MANAGEMENT

@app.on_message(filters.command("news"))
async def connect_news(client, message):
    chat_id = message.chat.id
    if not message.from_user or not is_admin(message.from_user.id):
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
    if not is_admin(message.from_user.id):
        return await app.send_message(message.chat.id, "You don't have permission.")
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    channels = config.get("news_channels", [])
    if not channels:
        return await app.send_message(message.chat.id, "No news channels added yet.")
    text = "**Configured News Channels:**\n\n" + "\n".join([f"- @{ch}" for ch in channels])
    await app.send_message(message.chat.id, text)

@app.on_message(filters.command("removenews"))
async def remove_news_channel(client, message):
    if not is_admin(message.from_user.id):
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

# RSS MANAGEMENT

@app.on_message(filters.command("addrss") & filters.private)
async def add_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to add RSS feeds.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addrss <rss_url>")
    rss_url = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if rss_url in feeds:
        return await message.reply("This RSS feed is already added.")
    feeds.append(rss_url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}}, upsert=True)
    await message.reply("RSS feed added successfully.")

@app.on_message(filters.command("removerss") & filters.private)
async def remove_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to remove RSS feeds.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removerss <rss_url>")
    rss_url = message.command[1].strip()
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if rss_url not in feeds:
        return await message.reply("This RSS feed is not in the list.")
    feeds.remove(rss_url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}})
    await message.reply("RSS feed removed successfully.")

@app.on_message(filters.command("listrss") & filters.private)
async def list_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to view RSS feeds.")
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    if not feeds:
        return await message.reply("No RSS feeds added yet.")
    text = "**Configured RSS Feeds:**\n\n" + "\n".join([f"- {url}" for url in feeds])
    await message.reply(text)

# ADMIN COMMANDS

@app.on_message(filters.command("addadmin") & filters.private)
async def add_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to add admins.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addadmin <user_id>")
    try:
        new_admin_id = int(message.command[1])
        if is_admin(new_admin_id):
            return await message.reply("This user is already an admin.")
        admins_col.insert_one({"user_id": new_admin_id})
        await message.reply(f"Added user {new_admin_id} as an admin.")
    except ValueError:
        await message.reply("Invalid user ID.")

@app.on_message(filters.command("removeadmin") & filters.private)
async def remove_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to remove admins.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removeadmin <user_id>")
    try:
        remove_id = int(message.command[1])
        if remove_id in ADMINS:
            return await message.reply("You cannot remove a static admin from config.")
        result = admins_col.delete_one({"user_id": remove_id})
        if result.deleted_count:
            await message.reply(f"Removed user {remove_id} from admins.")
        else:
            await message.reply("This user is not a dynamic admin.")
    except ValueError:
        await message.reply("Invalid user ID.")

@app.on_message(filters.command("listadmins") & filters.private)
async def list_admins(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not authorized to view admins.")
    static_admins = [str(uid) for uid in ADMINS]
    dynamic_admins = [str(admin["user_id"]) for admin in admins_col.find()]
    all_admins = static_admins + dynamic_admins
    await message.reply("**Current Admins:**\n" + "\n".join(all_admins))

# MAIN LOOP

async def main():
    await app.start()
    print("Bot is running...")

    try:
        await app.send_message(ADMINS[0], "<blockquote>✅ Bot has started successfully and is now running.</blockquote>")
    except Exception as e:
        print(f"Failed to send startup message: {e}")

    async def periodic_news_loop():
        while True:
            config = global_settings_collection.find_one({"_id": "config"}) or {}
            channels = config.get("news_channels", [])
            await fetch_and_send_news(app, db, channels, global_settings_collection)
            await asyncio.sleep(600)

    asyncio.create_task(periodic_news_loop())
    await idle()

if __name__ == '__main__':
    asyncio.run(main())
