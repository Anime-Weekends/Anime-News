import asyncio
import feedparser
from pyrogram import Client

async def fetch_and_send_news(app: Client, db, global_settings_collection):
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    news_channels = config.get("news_channels", [])
    rss_feeds = config.get("rss_feeds", [])

    if not news_channels or not rss_feeds:
        return

    sticker_file_id = "CAACAgUAAxkBAAEOP1Fn8vE65jQoZU-WKUd9NIZQy_W8CgAC2xQAAkczUFfhRns35IURtjYE"  # Change if needed

    for url in rss_feeds:
        feed = await asyncio.to_thread(feedparser.parse, url)
        entries = list(feed.entries)[::-1]  # newest last

        for entry in entries:
            entry_id = entry.get("id") or entry.get("link")
            if not db.sent_news.find_one({"entry_id": entry_id}):
                thumbnail_url = (
                    entry.get("media_thumbnail", [{}])[0].get("url")
                    if entry.get("media_thumbnail") else None
                )
                title = entry.get("title", "No Title")
                summary = entry.get("summary", "No summary available.")
                link = entry.get("link", "#")

                msg = (
                    f"<b><blockquote>💫 {title} 💫</blockquote>"
                    f"<blockquote>Bʏ @News_Stardust 🗞️</blockquote></b>\n\n"
                    f"<blockquote>✨ {summary}</blockquote>\n"
                    f"<blockquote><a href='{link}'>Rᴇᴀᴅ ᴍᴏʀᴇ</a></blockquote>"
                )

                for channel in news_channels:
                    try:
                        await asyncio.sleep(15)
                        if thumbnail_url:
                            await app.send_photo(chat_id=f"@{channel}", photo=thumbnail_url, caption=msg)
                        else:
                            await app.send_message(chat_id=f"@{channel}", text=msg)

                        await app.send_sticker(chat_id=f"@{channel}", sticker=sticker_file_id)

                        db.sent_news.insert_one({"entry_id": entry_id, "title": title, "link": link})
                        print(f"Sent news: {title} to @{channel}")
                    except Exception as e:
                        print(f"Error sending to @{channel}: {e}")
