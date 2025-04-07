# bot.py

from pyrofork import Client, filters
from pyrofork.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from rss import fetch_news
from anime_manga import get_anime_info, get_manga_info
from pymongo import MongoClient

bot = Client("autonews", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

mongo = MongoClient(MONGO_URI)
db = mongo["anime_news"]
admins_col = db["admins"]
rss_col = db["rss_channels"]
feeds_col = db["rss_feeds"]

# Utility
async def is_admin(uid): return uid == OWNER_ID or admins_col.find_one({"user_id": uid})
async def add_admin(uid): admins_col.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)
async def remove_admin(uid): admins_col.delete_one({"user_id": uid})
async def list_admins(): return [a["user_id"] for a in admins_col.find()]
async def add_rss_channel(cid): rss_col.update_one({"chat_id": cid}, {"$set": {"chat_id": cid}}, upsert=True)
async def list_rss_channels(): return [c["chat_id"] for c in rss_col.find()]
async def add_feed(url): feeds_col.update_one({"url": url}, {"$set": {"url": url}}, upsert=True)
async def remove_feed(url): feeds_col.delete_one({"url": url})
async def list_feeds(): return [f["url"] for f in feeds_col.find()]

# Start
@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply_photo(
        START_PIC,
        caption=(
            "**Welcome to AnimeNewsBot!**\n\n"
            "Get the latest anime/manga news from MyAnimeList!\n\n"
            "**Available Commands:**\n"
            "`/news` - Latest news\n"
            "`/anime <name>`\n"
            "`/manga <name>`\n"
            "`/addrss <url>`\n"
            "`/removerss <url>`\n"
            "`/rsslist`\n"
            "`/addadmin <id>`\n"
            "`/removeadmin <id>`\n"
            "`/adminlist`"
        ),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Support", url="https://t.me/Anime_Weekends")]]
        )
    )

# News
@bot.on_message(filters.command("news") & filters.group)
async def post_news(_, m: Message):
    chat_id, user_id = m.chat.id, m.from_user.id
    if not await is_admin(user_id): return await m.reply("🚫 You're not authorized.")
    await add_rss_channel(chat_id)
    await m.reply("📡 Fetching latest anime news...")
    feeds = list_feeds() or [URL_A]

    for feed in feeds:
        news_list = fetch_news(feed)
        for news in news_list:
            try:
                if news["image"]:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=news["image"],
                        caption=news["text"],
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🔗 Read More", url=news["link"])]]
                        )
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=news["text"],
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🔗 Read More", url=news["link"])]]
                        )
                    )
            except Exception as e:
                print(f"Error sending news: {e}")

# Admin Commands
@bot.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def addadmin(_, m: Message):
    if len(m.command) < 2: return await m.reply("Usage: `/addadmin <user_id>`", parse_mode="markdown")
    try:
        uid = int(m.command[1])
        await add_admin(uid)
        await m.reply(f"✅ Added `{uid}` as admin.", parse_mode="markdown")
    except Exception as e:
        await m.reply(f"❌ Error: {e}")

@bot.on_message(filters.command("removeadmin") & filters.user(OWNER_ID))
async def removeadmin(_, m: Message):
    if len(m.command) < 2: return await m.reply("Usage: `/removeadmin <user_id>`", parse_mode="markdown")
    try:
        uid = int(m.command[1])
        await remove_admin(uid)
        await m.reply(f"✅ Removed `{uid}` from admin list.", parse_mode="markdown")
    except Exception as e:
        await m.reply(f"❌ Error: {e}")

@bot.on_message(filters.command("adminlist") & filters.user(OWNER_ID))
async def listadmins(_, m: Message):
    admin_ids = await list_admins()
    if not admin_ids:
        return await m.reply("⚠️ No admins found.")
    await m.reply("**Admins:**\n" + "\n".join([f"`{i}`" for i in admin_ids]), parse_mode="markdown")

# RSS Management
@bot.on_message(filters.command("addrss") & filters.user(OWNER_ID))
async def addrss(_, m: Message):
    if len(m.command) < 2: return await m.reply("Usage: `/addrss <url>`", parse_mode="markdown")
    await add_feed(m.command[1])
    await m.reply(f"✅ Added RSS feed:\n`{m.command[1]}`", parse_mode="markdown")

@bot.on_message(filters.command("removerss") & filters.user(OWNER_ID))
async def removerss(_, m: Message):
    if len(m.command) < 2: return await m.reply("Usage: `/removerss <url>`", parse_mode="markdown")
    await remove_feed(m.command[1])
    await m.reply(f"🗑️ Removed feed:\n`{m.command[1]}`", parse_mode="markdown")

@bot.on_message(filters.command("rsslist") & filters.user(OWNER_ID))
async def rsslist(_, m: Message):
    feeds = await list_feeds()
    if not feeds:
        return await m.reply("⚠️ No RSS feeds added.")
    await m.reply("**Feeds:**\n" + "\n".join([f"`{f}`" for f in feeds]), parse_mode="markdown")

# Anime Command
@bot.on_message(filters.command("anime"))
async def anime(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("Usage: `/anime <name>`", parse_mode="markdown")
    query = " ".join(m.command[1:])
    result = get_anime_info(query)
    if not result: return await m.reply("❌ Anime not found.")
    await m.reply_photo(
        result["image"],
        caption=result["caption"],
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 View on MAL", url=result["url"])]]
        ),
        parse_mode="markdown"
    )

# Manga Command
@bot.on_message(filters.command("manga"))
async def manga(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("Usage: `/manga <name>`", parse_mode="markdown")
    query = " ".join(m.command[1:])
    result = get_manga_info(query)
    if not result: return await m.reply("❌ Manga not found.")
    await m.reply_photo(
        result["image"],
        caption=result["caption"],
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 View on MAL", url=result["url"])]]
        ),
        parse_mode="markdown"
    )

if __name__ == "__main__":
    bot.run()
