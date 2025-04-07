# rss.py

import aiohttp
import feedparser
from datetime import datetime, timedelta

posted_links = set()  # Memory cache to avoid reposting same news

async def fetch_rss_feed(session, url):
    try:
        async with session.get(url) as response:
            return feedparser.parse(await response.text())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def filter_recent_entries(entries, hours=6):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)
    recent = []

    for entry in entries:
        published = entry.get("published_parsed")
        if published:
            published_dt = datetime(*published[:6])
            if published_dt > cutoff:
                recent.append(entry)
    return recent

async def fetch_and_send_news(app, db, global_settings_collection):
    config = global_settings_collection.find_one({"_id": "config"}) or {}
    feeds = config.get("rss_feeds", [])
    channels = config.get("news_channels", [])

    if not feeds or not channels:
        return

    async with aiohttp.ClientSession() as session:
        for feed_url in feeds:
            parsed = await fetch_rss_feed(session, feed_url)
            if not parsed or not parsed.entries:
                continue

            recent_news = filter_recent_entries(parsed.entries)
            for entry in recent_news:
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                summary = entry.get("summary", "")
                if link in posted_links:
                    continue  # Skip already posted

                message = f"**{title}**\n\n{summary}\n\n[Read more]({link})"
                for channel in channels:
                    try:
                        await app.send_message(f"@{channel}", message, disable_web_page_preview=False)
                    except Exception as e:
                        print(f"Failed to send to @{channel}: {e}")
                posted_links.add(link)
