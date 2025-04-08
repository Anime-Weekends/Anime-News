import asyncio
import threading
import aiohttp
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN, START_PIC, MONGO_URI, ADMINS
from webhook import start_webhook
from modules.rss.rss import news_feed_loop
from modules.anilist import get_anime_info, get_manga_info

# Database
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["AnimeNewsBot"]
user_settings = db["user_settings"]
global_settings = db["global_settings"]
sent_news = db["sent_news"]

# Bot Client
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start webhook in a thread
threading.Thread(target=start_webhook, daemon=True).start()

# Util
def is_admin(user_id):
    return user_id in ADMINS

# Start Command
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user = message.from_user
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴍᴀɪɴ ʜᴜʙ", url="https://t.me/Bots_Nation"),
            InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ", url="https://t.me/Bots_Nation_Support")
        ],
        [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴩᴇʀ", url="https://t.me/darkxside78")]
    ])

    caption = (
        f"**» ʙᴀᴋᴋᴀᴀᴀ {user.mention}!!**\n\n"
        f"> ɪ ᴀᴍ ᴀɴ ᴀɴɪᴍᴇ ɴᴇᴡꜱ ʙᴏᴛ.\n"
        f"> ɪ ꜰᴇᴛᴄʜ ɴᴇᴡꜱ ꜰʀᴏᴍ ʀꜱꜱ ꜰᴇᴇᴅꜱ & ᴘᴏꜱᴛ ɪᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟꜱ.\n\n"
        f"_ᴜꜱᴇ /help ᴛᴏ ᴠɪᴇᴡ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅꜱ._"
    )

    await message.reply_photo(START_PIC, caption=caption, reply_markup=buttons)

# /news — Set News Channel
@app.on_message(filters.command("news"))
async def set_news_channel(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("🚫 You are not allowed to use this command.")
    
    if len(message.command) < 2:
        return await message.reply("Usage: `/news <channel_username>`", quote=True)

    channel = message.command[1].strip('@')
    global_settings.update_one({"_id": "config"}, {"$set": {"news_channel": channel}}, upsert=True)
    await message.reply(f"✅ News channel set to `@{channel}`")

# /addadmin
@app.on_message(filters.command("addadmin"))
async def add_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("🚫 You are not allowed to add admins.")
    
    if len(message.command) < 2:
        return await message.reply("Usage: `/addadmin <user_id>`")

    try:
        uid = int(message.command[1])
        if uid in ADMINS:
            return await message.reply("User is already an admin.")
        ADMINS.append(uid)
        await message.reply(f"✅ Added user `{uid}` to admin list.")
    except:
        await message.reply("❌ Invalid user ID.")

# /removeadmin
@app.on_message(filters.command("removeadmin"))
async def remove_admin(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("🚫 You are not allowed to remove admins.")

    if len(message.command) < 2:
        return await message.reply("Usage: `/removeadmin <user_id>`")

    try:
        uid = int(message.command[1])
        if uid not in ADMINS:
            return await message.reply("User is not an admin.")
        ADMINS.remove(uid)
        await message.reply(f"✅ Removed user `{uid}` from admin list.")
    except:
        await message.reply("❌ Invalid user ID.")

# /adminslist
@app.on_message(filters.command("adminslist"))
async def list_admins(client, message):
    admins_text = "\n".join([f"• `{uid}`" for uid in ADMINS])
    await message.reply(f"**Admin List:**\n\n{admins_text}")

# /addrss
@app.on_message(filters.command("addrss"))
async def add_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("🚫 You are not allowed to manage RSS.")

    if len(message.command) < 2:
        return await message.reply("Usage: `/addrss <rss_url>`")

    url = message.command[1]
    global_settings.update_one({"_id": "rss"}, {"$addToSet": {"feeds": url}}, upsert=True)
    await message.reply(f"✅ Added RSS feed:\n`{url}`")

# /removerss
@app.on_message(filters.command("removerss"))
async def remove_rss(client, message):
    if not is_admin(message.from_user.id):
        return await message.reply("🚫 You are not allowed to manage RSS.")

    if len(message.command) < 2:
        return await message.reply("Usage: `/removerss <rss_url>`")

    url = message.command[1]
    global_settings.update_one({"_id": "rss"}, {"$pull": {"feeds": url}})
    await message.reply(f"❌ Removed RSS feed:\n`{url}`")

# /listrss
@app.on_message(filters.command("listrss"))
async def list_rss(client, message):
    feeds_doc = global_settings.find_one({"_id": "rss"})
    feeds = feeds_doc.get("feeds", []) if feeds_doc else []

    if not feeds:
        return await message.reply("ℹ️ No RSS feeds found.")

    txt = "\n".join([f"• {url}" for url in feeds])
    await message.reply(f"**RSS Feed List:**\n\n{txt}")

# /anime
@app.on_message(filters.command("anime"))
async def anime_info(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/anime <name>`")

    name = " ".join(message.command[1:])
    data = await get_anime_info(name)

    if not data:
        return await message.reply("❌ No anime found.")

    await message.reply_photo(
        photo=data["image"],
        caption=f"**{data['title']}**\n\n> {data['description']}\n\nScore: `{data['score']}`\nEpisodes: `{data['episodes']}`\nStatus: `{data['status']}`\n\n[Read More]({data['url']})",
        disable_web_page_preview=False
    )

# /manga
@app.on_message(filters.command("manga"))
async def manga_info(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/manga <name>`")

    name = " ".join(message.command[1:])
    data = await get_manga_info(name)

    if not data:
        return await message.reply("❌ No manga found.")

    await message.reply_photo(
        photo=data["image"],
        caption=f"**{data['title']}**\n\n> {data['description']}\n\nScore: `{data['score']}`\nChapters: `{data['chapters']}`\nStatus: `{data['status']}`\n\n[Read More]({data['url']})",
        disable_web_page_preview=False
    )

# Main
async def main():
    await app.start()
    print("Bot is running...")

    rss_config = global_settings.find_one({"_id": "rss"})
    feeds = rss_config.get("feeds", []) if rss_config else []

    asyncio.create_task(news_feed_loop(app, db, global_settings, feeds))
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
