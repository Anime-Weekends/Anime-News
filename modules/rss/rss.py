import asyncio
import feedparser
from pyrogram import Client

async def fetch_and_send_news(app: Client, db, global_settings_collection, urls):
    config = global_settings_collection.find_one({"_id": "config"})
    if not config or "news_channel" not in config:
        return

    news_channel = "@" + config["news_channel"]
    sticker_file_id = "CAACAgUAAxkBAAEB..."  # Replace this with your actual sticker file ID

    for url in urls:
        feed = await asyncio.to_thread(feedparser.parse, url)
        entries = list(feed.entries)[::-1]  # Reverse order to send newest last

        for entry in entries:
            entry_id = entry.get('id', entry.get('link'))

            if not db.sent_news.find_one({"entry_id": entry_id}):
                thumbnail_url = entry.media_thumbnail[0]['url'] if 'media_thumbnail' in entry else None
                msg = f"<b>**<blockquote>💫 {entry.title} 💫</blockquote>\n<blockquote>Bʏ @News_Stardust 🗞️</blockquote>**</b>\n\n<blockquote expandable>✨ {entry.summary if 'summary' in entry else ''}</blockquote>\n<blockquote><a href='{entry.link}'>Rᴇᴀᴅ ᴍᴏʀᴇ</blockquote></a>"

                try:
                    await asyncio.sleep(15)  # Delay between messages
                    if thumbnail_url:
                        await app.send_photo(chat_id=news_channel, photo=thumbnail_url, caption=msg)
                    else:
                        await app.send_message(chat_id=news_channel, text=msg)

                    # Send a sticker after the message
                    await app.send_sticker(chat_id=news_channel, sticker=sticker_file_id)

                    db.sent_news.insert_one({"entry_id": entry_id, "title": entry.title, "link": entry.link})
                    print(f"Sent news: {entry.title}")
                except Exception as e:
                    print(f"Error sending news message: {e}")

# Background loop function
async def news_feed_loop(app: Client, db, global_settings_collection, urls):
    while True:
        try:
            await fetch_and_send_news(app, db, global_settings_collection, urls)
        except Exception as e:
            print(f"Error in news_feed_loop: {e}")
        await asyncio.sleep(300)  # Wait 5 minutes
