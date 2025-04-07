from pyrogram import Client, filters
from pyrogram.types import Message
from config import (
    BOT_TOKEN, API_ID, API_HASH,
    ADMINS, URL_A, OWNER_ID,
    START_PIC, MONGO_URI
)
from pymongo import MongoClient
import feedparser

# Initialize bot client
client = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Setup MongoDB
mongo = MongoClient(MONGO_URI)
db = mongo.anime_news
db_admins = db.admins
db_rss = db.rss
db_channels = db.rss_channels

# Check admin
def is_admin(user_id):
    return user_id == OWNER_ID or db_admins.find_one({"_id": user_id})

# /start command
@client.on_message(filters.command("start"))
async def start_handler(_, message: Message):
    await message.reply_photo(
        START_PIC,
        caption="Welcome to Anime News Bot!\n\nUse /help to see all commands."
    )

# /help command
@client.on_message(filters.command("help"))
async def help_handler(_, message: Message):
    await message.reply_text("""
**Admin Commands:**
/addadmin [user_id] - Add an admin
/removeadmin [user_id] - Remove an admin
/adminlist - List all admins

**RSS Commands:**
/addrss [rss_url] - Add RSS feed URL
/removerss [rss_url] - Remove RSS feed URL
/listrss - List all RSS feeds

**News Command:**
/news - Add this channel for anime news updates
""")

# /addadmin command
@client.on_message(filters.command("addadmin"))
async def add_admin(_, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    if len(message.command) < 2:
        return await message.reply("Please provide a user ID.")
    user_id = int(message.command[1])
    db_admins.update_one({"_id": user_id}, {"$set": {"admin": True}}, upsert=True)
    await message.reply(f"User {user_id} added as admin.")

# /removeadmin command
@client.on_message(filters.command("removeadmin"))
async def remove_admin(_, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    if len(message.command) < 2:
        return await message.reply("Please provide a user ID.")
    user_id = int(message.command[1])
    db_admins.delete_one({"_id": user_id})
    await message.reply(f"User {user_id} removed from admin list.")

# /adminlist command
@client.on_message(filters.command("adminlist"))
async def admin_list(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    admins = [str(doc['_id']) for doc in db_admins.find()]
    admins.append(str(OWNER_ID))
    await message.reply("Admins:\n" + "\n".join(admins))

# /addrss command
@client.on_message(filters.command("addrss"))
async def add_rss(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply("Please provide an RSS URL.")
    url = message.command[1]
    db_rss.update_one({"_id": url}, {"$set": {"url": url}}, upsert=True)
    await message.reply("RSS feed added.")

# /removerss command
@client.on_message(filters.command("removerss"))
async def remove_rss(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply("Please provide an RSS URL to remove.")
    url = message.command[1]
    db_rss.delete_one({"_id": url})
    await message.reply("RSS feed removed.")

# /listrss command
@client.on_message(filters.command("listrss"))
async def list_rss(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    feeds = [doc['_id'] for doc in db_rss.find()]
    if feeds:
        await message.reply("RSS Feeds:\n" + "\n".join(feeds))
    else:
        await message.reply("No RSS feeds found.")

# /news command
@client.on_message(filters.command("news"))
async def add_news_channel(_, message: Message):
    if not is_admin(message.from_user.id):
        return
    chat_id = message.chat.id
    db_channels.update_one({"_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)
    await message.reply("This chat has been added for anime news updates.")

# Run the bot
client.run()
