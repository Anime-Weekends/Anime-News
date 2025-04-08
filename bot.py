import asyncio
import threading
import aiohttp
import feedparser
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_ID, API_HASH, BOT_TOKEN, START_PIC, MONGO_URI, ADMINS
from webhook import start_webhook
from modules.rss.rss import news_feed_loop

# DB
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["AnimeNewsBot"]
users = db["user_settings"]
global_config = db["global_settings"]
sent_news = db["sent_news"]

# BOT
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# WEBHOOK
threading.Thread(target=start_webhook, daemon=True).start()

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_photo(
        photo=START_PIC,
        caption=(
            f"**ᴏʜᴀʏᴏᴜ {message.from_user.first_name}**\n\n"
            f"> ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡs ʙᴏᴛ.\n"
            f"> ɪ ᴘᴏsᴛ ʟᴀᴛᴇsᴛ ʀss ɴᴇᴡs ᴛᴏ sᴇᴛ ᴄʜᴀɴɴᴇʟs.\n"
            f"> ᴜsᴇ /news ᴛᴏ ᴀᴅᴅ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ᴜᴘᴅᴀᴛᴇs."
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Support", url="https://t.me/Bots_Nation_Support"),
             InlineKeyboardButton("💬 Dev", url="https://t.me/darkxside78")],
        ])
    )

# SET NEWS CHANNEL
@app.on_message(filters.command("news"))
async def set_news_channel(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ You don't have permission.")
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: /news <channel_username>")
    
    channel = message.command[1].lstrip("@")
    global_config.update_one({"_id": "config"}, {"$set": {"news_channel": channel}}, upsert=True)
    await message.reply(f"✅ News channel set to: `@{channel}`")

# ADMIN MANAGEMENT
@app.on_message(filters.command("addadmin"))
async def add_admin(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply("Usage: /addadmin <user_id>")
    new_admin = int(message.command[1])
    if new_admin in ADMINS:
        return await message.reply("Already an admin.")
    ADMINS.append(new_admin)
    await message.reply(f"✅ Added admin: `{new_admin}`")

@app.on_message(filters.command("removeadmin"))
async def remove_admin(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply("Usage: /removeadmin <user_id>")
    rem_admin = int(message.command[1])
    if rem_admin in ADMINS:
        ADMINS.remove(rem_admin)
        await message.reply(f"✅ Removed admin: `{rem_admin}`")
    else:
        await message.reply("Not an admin.")

@app.on_message(filters.command("adminslist"))
async def list_admins(client, message):
    text = "**👑 Admins List:**\n\n" + "\n".join([f"> `{admin_id}`" for admin_id in ADMINS])
    await message.reply(text)

# RSS MANAGEMENT
@app.on_message(filters.command("addrss"))
async def add_rss(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply("Usage: /addrss <rss_url>")
    rss_url = message.command[1]
    global_config.update_one({"_id": "rss_feeds"}, {"$addToSet": {"feeds": rss_url}}, upsert=True)
    await message.reply(f"✅ Added RSS feed:\n```{rss_url}```")

@app.on_message(filters.command("removerss"))
async def remove_rss(client, message):
    if message.from_user.id not in ADMINS:
        return
    if len(message.command) < 2:
        return await message.reply("Usage: /removerss <rss_url>")
    rss_url = message.command[1]
    global_config.update_one({"_id": "rss_feeds"}, {"$pull": {"feeds": rss_url}})
    await message.reply(f"✅ Removed RSS feed:\n```{rss_url}```")

@app.on_message(filters.command("listrss"))
async def list_rss(client, message):
    data = global_config.find_one({"_id": "rss_feeds"}) or {}
    feeds = data.get("feeds", [])
    if not feeds:
        return await message.reply("No RSS feeds added.")
    text = "**📡 Current RSS Feeds:**\n\n" + "\n".join([f"> `{url}`" for url in feeds])
    await message.reply(text)

# ANIME / MANGA MOCK
@app.on_message(filters.command("anime"))
async def anime_search(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /anime <name>")
    name = " ".join(message.command[1:])
    await message.reply_photo(
        photo="https://cdn.myanimelist.net/images/anime/4/19644.jpg",
        caption=f"**🔍 Anime Search:**\n\n> **Title:** {name}\n> **Episodes:** 12\n> **Status:** Finished\n> [More Info](https://myanimelist.net)"
    )

@app.on_message(filters.command("manga"))
async def manga_search(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /manga <name>")
    name = " ".join(message.command[1:])
    await message.reply_photo(
        photo="https://cdn.myanimelist.net/images/manga/2/253146.jpg",
        caption=f"**🔍 Manga Search:**\n\n> **Title:** {name}\n> **Chapters:** 45\n> **Status:** Ongoing\n> [More Info](https://myanimelist.net)"
    )

# MAIN LOOP
async def main():
    await app.start()
    print("✅ Bot is running...")
    config = global_config.find_one({"_id": "rss_feeds"}) or {}
    feeds = config.get("feeds", [])
    asyncio.create_task(news_feed_loop(app, db, global_config, feeds))
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
