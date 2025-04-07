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
global_settings_collection = db["global_settings"]
admins_col = db["admins"]

# Pyrogram bot setup
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Flask webhook
threading.Thread(target=start_webhook, daemon=True).start()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS or admins_col.find_one({"user_id": user_id}) is not None

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    username = message.from_user.username or "User"
    await message.reply_photo(
        photo=START_PIC,
        caption=(
            f"**<blockquote>ʙᴀᴋᴋᴀᴀᴀ {username} !!!</blockquote>**\n"
            f"**ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡs ʙᴏᴛ.**\n"
            f"**ɪ ғᴇᴛᴄʜ ʀss ɴᴇᴡs ᴀɴᴅ ᴘᴏsᴛ ɪᴛ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ.**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Main Hub", url="https://t.me/RexySama"),
             InlineKeyboardButton("Support", url="https://t.me/RexySama")],
            [InlineKeyboardButton("Developer", url="https://t.me/RexySama")]
        ])
    )

# Admin commands
@app.on_message(filters.command("addadmin") & filters.private)
async def add_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addadmin <user_id>")
    uid = int(message.command[1])
    if is_admin(uid):
        return await message.reply("Already admin.")
    admins_col.insert_one({"user_id": uid})
    await message.reply(f"Added {uid} as admin.")

@app.on_message(filters.command("removeadmin") & filters.private)
async def remove_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removeadmin <user_id>")
    uid = int(message.command[1])
    if uid in ADMINS:
        return await message.reply("Can't remove static admin.")
    result = admins_col.delete_one({"user_id": uid})
    await message.reply("Removed." if result.deleted_count else "Not found.")

@app.on_message(filters.command("adminlist") & filters.private)
async def list_admins(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    static_admins = [str(a) for a in ADMINS]
    dynamic_admins = [str(a["user_id"]) for a in admins_col.find()]
    await message.reply("**Admins:**\n" + "\n".join(static_admins + dynamic_admins))

# RSS Management
@app.on_message(filters.command("addrss") & filters.private)
async def addrss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addrss <url>")
    url = message.command[1]
    cfg = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = cfg.get("rss_feeds", [])
    if url in feeds:
        return await message.reply("Already added.")
    feeds.append(url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}}, upsert=True)
    await message.reply("Feed added.")

@app.on_message(filters.command("removerss") & filters.private)
async def removerss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removerss <url>")
    url = message.command[1]
    cfg = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = cfg.get("rss_feeds", [])
    if url not in feeds:
        return await message.reply("Not found.")
    feeds.remove(url)
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"rss_feeds": feeds}})
    await message.reply("Feed removed.")

@app.on_message(filters.command("listrss") & filters.private)
async def listrss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    cfg = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = cfg.get("rss_feeds", [])
    if not feeds:
        return await message.reply("No feeds.")
    await message.reply("**Feeds:**\n" + "\n".join(feeds))

# News command
@app.on_message(filters.command("news") & filters.private)
async def post_news(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("Unauthorized.")
    await message.reply("Fetching latest news...")
    await fetch_and_send_news(app, db, global_settings_collection)

# Bot loop
async def main():
    await app.start()
    print("Bot is running...")
    try:
        await app.send_message(ADMINS[0], "✅ Bot started.")
    except Exception as e:
        print(f"Startup message failed: {e}")

    async def loop_news():
        while True:
            await fetch_and_send_news(app, db, global_settings_collection)
            await asyncio.sleep(600)

    asyncio.create_task(loop_news())
    await idle()

if __name__ == '__main__':
    asyncio.run(main())
