# rss.py

import feedparser
import requests
from bs4 import BeautifulSoup

def fetch_news(feed_url):
    parsed_feed = feedparser.parse(feed_url)
    news_items = []

    for entry in parsed_feed.entries[:5]:  # Fetch latest 5
        title = entry.get("title", "No title")
        link = entry.get("link", "")
        published = entry.get("published", "Unknown date")
        author = entry.get("author", "Unknown author")
        categories = [cat.term for cat in entry.get("tags", [])]
        category_text = ", ".join(categories) if categories else "None"

        # Clean HTML summary
        summary_html = entry.get("summary", "")
        summary_text = BeautifulSoup(summary_html, "html.parser").text.strip()

        # Truncate long summary
        if len(summary_text) > 500:
            summary_text = summary_text[:500] + "... [Read more](" + link + ")"

        # Try to extract image (from summary or media content)
        image_url = None
        soup = BeautifulSoup(summary_html, "html.parser")
        img_tag = soup.find("img")
        if img_tag:
            image_url = img_tag.get("src")

        # Format for Telegram (Markdown)
        formatted_text = (
            f"📰 **[{title}]({link})**\n"
            f"👤 *Author:* `{author}`\n"
            f"🗂️ *Category:* `{category_text}`\n"
            f"🗓️ *Published:* `{published}`\n\n"
            f"{summary_text}"
        )

        news_items.append({
            "title": title,
            "link": link,
            "summary": summary_text,
            "image": image_url,
            "text": formatted_text
        })

    return news_items
