import asyncio
import feedparser
from pyrogram import Client

async def fetch_and_send_news(app: Client, db, global_settings_collection, urls):
    config = global_settings_collection.find_one({"_id": "config"})
    if not config or "news_channel" not in config:
        return

    news_channel = "@" + config["news_channel"]

    for url in urls:
        feed = await asyncio.to_thread(feedparser.parse, url)
        entries = list(feed.entries)[::-1]

        for entry in entries:
            entry_id = entry.get('id', entry.get('link'))
            if db.sent_news.find_one({"entry_id": entry_id}):
                continue

            title = entry.title.replace("-", "\\-").replace(".", "\\.")
            summary = entry.summary if "summary" in entry else "No summary available"
            summary = summary.replace("-", "\\-").replace(".", "\\.")
            link = entry.link
            thumbnail = entry.media_thumbnail[0]['url'] if 'media_thumbnail' in entry else None

            msg = (
                f"> *{title}*\n\n"
                f"> {summary}\n\n"
                f"[Read more]({link})"
            )

            try:
                await asyncio.sleep(15)
                if thumbnail:
                    await app.send_photo(news_channel, thumbnail, caption=msg, parse_mode="MarkdownV2")
                else:
                    await app.send_message(news_channel, msg, parse_mode="MarkdownV2")
                db.sent_news.insert_one({"entry_id": entry_id})
            except Exception as e:
                print(f"Failed to send news: {e}")

async def news_feed_loop(app, db, global_settings_collection, urls):
    while True:
        await fetch_and_send_news(app, db, global_settings_collection, urls)
        await asyncio.sleep(30)
