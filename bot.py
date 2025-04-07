import asyncio
from pyrofork import Client, filters
from pyrofork.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, OWNER_ID, ADMINS, URL_A, START_PIC
from rss import fetch_news
from anime_manga import get_anime_info, get_manga_info

app = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoClient(MONGO_URI)["anime_bot"]
channels_col = db["channels"]
admins_col = db["admins"]
rss_col = db["rss_feeds"]

# Helper
def is_admin(user_id):
    return user_id == OWNER_ID or user_id in ADMINS or admins_col.find_one({"_id": user_id}) is not None

# Start
@app.on_message(filters.command("start"))
async def start_cmd(_, msg: Message):
    await msg.reply_photo(
        START_PIC,
        caption="**Welcome to AnimeNewsBot!**\nGet the latest anime news and more.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Latest News", callback_data="get_news")],
            [InlineKeyboardButton("Source Code", url="https://github.com/Anime-Weekends/AutoNews-V2-")]
        ])
    )

# News
@app.on_message(filters.command("news"))
async def news_cmd(_, msg: Message):
    if not msg.chat.type.endswith("channel") and not is_admin(msg.from_user.id):
        return await msg.reply("Only admins or channels can use this command.")

    if channels_col.find_one({"_id": msg.chat.id}) is None:
        channels_col.insert_one({"_id": msg.chat.id})

    feeds = [f["url"] for f in rss_col.find()] or [URL_A]
    for feed in feeds:
        news_items = fetch_news(feed)
        for item in news_items:
            await msg.reply_photo(
                item["image"] or START_PIC,
                caption=f'{item["text"]}\n\n[Read More]({item["link"]})',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Read More", url=item["link"])]
                ])
            )
            await asyncio.sleep(1)

# Anime Info
@app.on_message(filters.command("anime"))
async def anime_cmd(_, msg: Message):
    query = msg.text.split(None, 1)[1] if len(msg.command) > 1 else None
    if not query:
        return await msg.reply("Usage: /anime <anime name>")

    info = get_anime_info(query)
    if not info:
        return await msg.reply("No results found.")
    
    await msg.reply_photo(
        info["image"],
        caption=info["caption"],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("MyAnimeList", url=info["url"])]])
    )

# Manga Info
@app.on_message(filters.command("manga"))
async def manga_cmd(_, msg: Message):
    query = msg.text.split(None, 1)[1] if len(msg.command) > 1 else None
    if not query:
        return await msg.reply("Usage: /manga <manga name>")

    info = get_manga_info(query)
    if not info:
        return await msg.reply("No results found.")
    
    await msg.reply_photo(
        info["image"],
        caption=info["caption"],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("MyAnimeList", url=info["url"])]])
    )

# Admin Management
@app.on_message(filters.command("addadmin"))
async def add_admin(_, msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.reply("You don't have permission.")

    try:
        user_id = int(msg.text.split()[1])
        admins_col.insert_one({"_id": user_id})
        await msg.reply(f"User `{user_id}` added as admin.")
    except:
        await msg.reply("Usage: /addadmin <user_id>")

@app.on_message(filters.command("removeadmin"))
async def remove_admin(_, msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.reply("You don't have permission.")
    
    try:
        user_id = int(msg.text.split()[1])
        admins_col.delete_one({"_id": user_id})
        await msg.reply(f"User `{user_id}` removed from admins.")
    except:
        await msg.reply("Usage: /removeadmin <user_id>")

@app.on_message(filters.command("adminlist"))
async def admin_list(_, msg: Message):
    admin_ids = [admin["_id"] for admin in admins_col.find()]
    admin_ids.extend(ADMINS)
    text = "**Admins:**\n" + "\n".join(map(str, set(admin_ids)))
    await msg.reply(text)

# RSS Management
@app.on_message(filters.command("addrss"))
async def add_rss(_, msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.reply("You don't have permission.")
    try:
        url = msg.text.split(None, 1)[1]
        rss_col.insert_one({"url": url})
        await msg.reply("RSS feed added.")
    except:
        await msg.reply("Usage: /addrss <rss_url>")

@app.on_message(filters.command("removerss"))
async def remove_rss(_, msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.reply("You don't have permission.")
    try:
        url = msg.text.split(None, 1)[1]
        rss_col.delete_one({"url": url})
        await msg.reply("RSS feed removed.")
    except:
        await msg.reply("Usage: /removerss <rss_url>")

@app.on_message(filters.command("rsslist"))
async def list_rss(_, msg: Message):
    feeds = rss_col.find()
    text = "**RSS Feeds:**\n" + "\n".join(f["url"] for f in feeds)
    await msg.reply(text or "No feeds found.")

# Callback for /start button
@app.on_callback_query(filters.regex("get_news"))
async def news_callback(_, cb):
    await news_cmd(_, cb.message)
    await cb.answer()

# Run bot
if __name__ == "__main__":
    app.run()
