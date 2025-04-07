# bot.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from rss import fetch_news
from pymongo import MongoClient
import requests

mongo = MongoClient(MONGO_URI)
db = mongo["AutoNewsBot"]
admin_col = db["admins"]
channel_col = db["channels"]
rss_col = db["rssfeeds"]

app = Client("autonews", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure owner is in admin list
if not admin_col.find_one({"user_id": OWNER_ID}):
    admin_col.insert_one({"user_id": OWNER_ID})

def is_admin(user_id):
    return admin_col.find_one({"user_id": user_id}) is not None

# /start
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_photo(
        START_PIC,
        caption=f"**Hello {message.from_user.first_name}!**\n\n"
                "I'm your Anime Auto News Bot!\n\nUse /help to get started.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("News Feed", url="https://myanimelist.net/news")],
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

# /help
@app.on_message(filters.command("help"))
async def help_cmd(client, message: Message):
    await message.reply_photo(
        START_PIC,
        caption=(
            "**Available Commands:**\n\n"
            "📰 /news – Post latest anime news\n"
            "📚 /anime <name> – Get anime info\n"
            "📖 /manga <name> – Get manga info\n"
            "➕ /addrss <url> – Add a feed\n"
            "➖ /removerss <url> – Remove feed\n"
            "📃 /listrss – List feeds\n"
            "👑 /addadmin <id>, /removeadmin <id>, /adminlist"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Source Code", url="https://github.com/Anime-Weekends/AutoNews-V2-")]
        ])
    )

# /news
@app.on_message(filters.command("news"))
async def news_cmd(client, message: Message):
    if message.chat.type in ["supergroup", "group"]:
        if not is_admin(message.from_user.id):
            return await message.reply("❌ Only admins can use this in groups.")
        channel_col.update_one({"chat_id": message.chat.id}, {"$set": {"chat_id": message.chat.id}}, upsert=True)

    feeds = rss_col.find() or [{"url": URL_A}]
    for feed in feeds:
        news_items = fetch_news(feed["url"])
        for item in news_items:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("Read More", url=item["link"])]])
            if item["image"]:
                await message.reply_photo(item["image"], caption=item["text"], reply_markup=btn)
            else:
                await message.reply(item["text"], reply_markup=btn)

# /anime
@app.on_message(filters.command("anime"))
async def anime_cmd(client, message: Message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await message.reply("Please provide an anime name.")
    name = query[1]
    res = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1").json()
    if not res.get("data"):
        return await message.reply("No anime found.")
    anime = res["data"][0]
    text = (
        f"**{anime['title']}**\n"
        f"📅 Aired: `{anime['aired']['string']}`\n"
        f"🎭 Genres: {', '.join([g['name'] for g in anime['genres']])}\n"
        f"⭐ Score: `{anime['score']}`\n"
        f"📺 Episodes: `{anime['episodes']}`\n"
        f"✍️ Status: `{anime['status']}`\n\n"
        f"__{anime['synopsis'][:500]}__..."
    )
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("More Info", url=anime["url"])]])
    await message.reply_photo(anime["images"]["jpg"]["image_url"], caption=text, reply_markup=btn)

# /manga
@app.on_message(filters.command("manga"))
async def manga_cmd(client, message: Message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return await message.reply("Please provide a manga name.")
    name = query[1]
    res = requests.get(f"https://api.jikan.moe/v4/manga?q={name}&limit=1").json()
    if not res.get("data"):
        return await message.reply("No manga found.")
    manga = res["data"][0]
    text = (
        f"**{manga['title']}**\n"
        f"🗓️ Published: `{manga['published']['string']}`\n"
        f"🎭 Genres: {', '.join([g['name'] for g in manga['genres']])}\n"
        f"⭐ Score: `{manga['score']}`\n"
        f"📚 Volumes: `{manga['volumes']}`\n"
        f"✍️ Status: `{manga['status']}`\n\n"
        f"__{manga['synopsis'][:500]}__..."
    )
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("More Info", url=manga["url"])]])
    await message.reply_photo(manga["images"]["jpg"]["image_url"], caption=text, reply_markup=btn)

# Admin Commands
@app.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /addadmin <user_id>")
    try:
        uid = int(message.command[1])
        if admin_col.find_one({"user_id": uid}):
            return await message.reply("Already an admin.")
        admin_col.insert_one({"user_id": uid})
        await message.reply("Admin added.")
    except:
        await message.reply("Invalid user ID.")

@app.on_message(filters.command("removeadmin") & filters.user(OWNER_ID))
async def remove_admin(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /removeadmin <user_id>")
    try:
        uid = int(message.command[1])
        if not admin_col.find_one({"user_id": uid}):
            return await message.reply("User is not an admin.")
        admin_col.delete_one({"user_id": uid})
        await message.reply("Admin removed.")
    except:
        await message.reply("Invalid user ID.")

@app.on_message(filters.command("adminlist"))
async def admin_list(client, message: Message):
    admins = [str(a["user_id"]) for a in admin_col.find()]
    await message.reply(f"**Admins:**\n" + "\n".join(admins))

# RSS Commands
@app.on_message(filters.command("addrss"))
async def addrss(client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not an admin.")
    if len(message.command) < 2:
        return await message.reply("Usage: /addrss <url>")
    url = message.command[1]
    rss_col.update_one({"url": url}, {"$set": {"url": url}}, upsert=True)
    await message.reply("RSS feed added.")

@app.on_message(filters.command("removerss"))
async def removerss(client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not an admin.")
    if len(message.command) < 2:
        return await message.reply("Usage: /removerss <url>")
    url = message.command[1]
    rss_col.delete_one({"url": url})
    await message.reply("RSS feed removed.")

@app.on_message(filters.command("listrss"))
async def listrss(client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You're not an admin.")
    feeds = [r["url"] for r in rss_col.find()]
    if not feeds:
        return await message.reply("No RSS feeds added.")
    await message.reply("**RSS Feeds:**\n" + "\n".join(feeds))

# Run
app.run()
