from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, ADMINS, URL_A
from rss import fetch_and_format_rss
from pymongo import MongoClient
from config import MONGO_URI

client = Client("AnimeNewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

mongo = MongoClient(MONGO_URI)
db = mongo.anime_news
admin_col = db.admins
rss_col = db.rss_links

# Ensure OWNER is in admin list
if admin_col.count_documents({}) == 0:
    admin_col.insert_one({"admin_id": OWNER_ID})

# Check if user is admin
def is_admin(user_id):
    return admin_col.find_one({"admin_id": user_id}) is not None

@client.on_message(filters.command("start"))
async def start_handler(_, message: Message):
    await message.reply_photo(
        photo="https://i.ibb.co/ynjcqYdZ/photo-2025-04-06-20-48-47-7490304985767346192.jpg",
        caption="Welcome to AnimeNewsBot!\nUse /news to get latest anime news.\nAdmins can manage feeds with /addrss, /removerss, etc."
    )

# ADMIN COMMANDS
@client.on_message(filters.command("addadmin"))
async def add_admin(_, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You are not authorized.")

    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply("Usage: /addadmin <user_id>")

    new_admin = int(message.command[1])
    if is_admin(new_admin):
        return await message.reply("User is already an admin.")

    admin_col.insert_one({"admin_id": new_admin})
    await message.reply("Admin added.")

@client.on_message(filters.command("removeadmin"))
async def remove_admin(_, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You are not authorized.")

    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply("Usage: /removeadmin <user_id>")

    admin_id = int(message.command[1])
    if admin_id == OWNER_ID:
        return await message.reply("Cannot remove the owner.")
    admin_col.delete_one({"admin_id": admin_id})
    await message.reply("Admin removed.")

@client.on_message(filters.command("adminlist"))
async def admin_list(_, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You are not authorized.")

    admins = [str(admin["admin_id"]) for admin in admin_col.find()]
    await message.reply("Admins:\n" + "\n".join(admins))

# RSS COMMANDS
@client.on_message(filters.command("addrss"))
async def add_rss(_, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You are not authorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /addrss <url>")

    url = message.command[1]
    if rss_col.find_one({"url": url}):
        return await message.reply("This RSS feed already exists.")
    rss_col.insert_one({"url": url})
    await message.reply("RSS feed added.")

@client.on_message(filters.command("removerss"))
async def remove_rss(_, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply("You are not authorized.")
    if len(message.command) != 2:
        return await message.reply("Usage: /removerss <url>")

    url = message.command[1]
    rss_col.delete_one({"url": url})
    await message.reply("RSS feed removed.")

@client.on_message(filters.command("listrss"))
async def list_rss(_, message: Message):
    feeds = rss_col.find()
    urls = [feed["url"] for feed in feeds]
    if not urls:
        return await message.reply("No RSS feeds added.")
    await message.reply("RSS Feeds:\n" + "\n".join(urls))

@client.on_message(filters.command("news"))
async def post_news(_, message: Message):
    feeds = rss_col.find()
    if feeds.count() == 0:
        # fallback to default MAL feed
        urls = [URL_A]
    else:
        urls = [f["url"] for f in feeds]

    for url in urls:
        entries = await fetch_and_format_rss(url)
        for entry in entries:
            await message.reply(entry)
