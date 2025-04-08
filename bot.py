import asyncio
import threading
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from webhook import start_webhook
from modules.rss.rss import news_feed_loop
from modules.anilist import search_anilist

mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["AnimeNewsBot"]
user_settings_collection = db["user_settings"]
global_settings_collection = db["global_settings"]
app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

threading.Thread(target=start_webhook, daemon=True).start()

@app.on_message(filters.command("start"))
async def start_cmd(_, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Updates", url="https://t.me/Bots_Nation")],
        [InlineKeyboardButton("Developer", url="https://t.me/darkxside78")]
    ])
    msg = (
        f"> *Hello {message.from_user.first_name}\\!* \n\n"
        f"> *I fetch anime news from RSS feeds and post them to configured channels automatically\\.*\n"
        f"> *Use /help to see commands\\.*"
    )
    await message.reply_photo(START_PIC, caption=msg, reply_markup=buttons, parse_mode="MarkdownV2")

@app.on_message(filters.command("news"))
async def set_news_channel(_, message):
    if message.from_user.id not in ADMINS:
        return await message.reply("⛔ Only admins can use this command.")
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Usage: `/news <channel_username>`", parse_mode="MarkdownV2")
    global_settings_collection.update_one({"_id": "config"}, {"$set": {"news_channel": args[1]}}, upsert=True)
    await message.reply(f"> ✅ News channel set to: `{args[1]}`", parse_mode="MarkdownV2")

@app.on_message(filters.command("anime"))
async def anime_cmd(_, message):
    query = " ".join(message.text.split()[1:])
    if not query:
        return await message.reply("Usage: `/anime <name>`", parse_mode="MarkdownV2")
    result = await search_anilist(query, "ANIME")
    if not result:
        return await message.reply("Not found.")
    msg = f"> *{result['title']['romaji']}*\n\n>{result['description'][:300]}...\n\n[More info]({result['siteUrl']})"
    await message.reply_photo(result["coverImage"]["large"], caption=msg, parse_mode="MarkdownV2")

@app.on_message(filters.command("manga"))
async def manga_cmd(_, message):
    query = " ".join(message.text.split()[1:])
    if not query:
        return await message.reply("Usage: `/manga <name>`", parse_mode="MarkdownV2")
    result = await search_anilist(query, "MANGA")
    if not result:
        return await message.reply("Not found.")
    msg = f"> *{result['title']['romaji']}*\n\n>{result['description'][:300]}...\n\n[More info]({result['siteUrl']})"
    await message.reply_photo(result["coverImage"]["large"], caption=msg, parse_mode="MarkdownV2")

@app.on_message(filters.command(["addadmin", "removeadmin", "adminslist"]))
async def manage_admins(_, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("Only owner can manage admins.")
    cmd = message.command[0]
    if cmd == "addadmin":
        uid = int(message.text.split()[1])
        if uid not in ADMINS:
            ADMINS.append(uid)
        await message.reply("Admin added.")
    elif cmd == "removeadmin":
        uid = int(message.text.split()[1])
        if uid in ADMINS:
            ADMINS.remove(uid)
        await message.reply("Admin removed.")
    elif cmd == "adminslist":
        admin_list = "\n".join(f"`{x}`" for x in ADMINS)
        await message.reply(f"Current admins:\n{admin_list}", parse_mode="MarkdownV2")

@app.on_message(filters.command(["addrss", "removerss", "listrss"]))
async def rss_manage(_, message):
    if message.from_user.id not in ADMINS:
        return await message.reply("Only admins can manage RSS feeds.")
    cmd = message.command[0]
    if cmd == "addrss":
        url = message.text.split()[1]
        db.rss.insert_one({"url": url})
        await message.reply("RSS feed added.")
    elif cmd == "removerss":
        url = message.text.split()[1]
        db.rss.delete_one({"url": url})
        await message.reply("RSS feed removed.")
    elif cmd == "listrss":
        urls = [doc["url"] for doc in db.rss.find()]
        await message.reply("Current RSS feeds:\n" + "\n".join(f"- `{u}`" for u in urls), parse_mode="MarkdownV2")

async def main():
    await app.start()
    print("Bot running...")
    urls = [URL_A] + [doc["url"] for doc in db.rss.find()]
    asyncio.create_task(news_feed_loop(app, db, global_settings_collection, urls))
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
