# rss.py

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_news(feed_url):
    feed = feedparser.parse(feed_url)
    news_items = []

    for entry in feed.entries[:3]:  # Limit to 3 latest
        title = entry.title
        link = entry.link
        published = format_date(entry.get("published", "Unknown"))
        summary = clean_summary(entry.summary)
        image = extract_image(entry.summary)

        caption = (
            f"**📰 {title}**\n\n"
            f"**🗓️ Published:** `{published}`\n"
            f"**🌐 Source:** [Visit Link]({link})\n\n"
            f"__{summary}__"
        )

        news_items.append({
            "title": title,
            "link": link,
            "text": caption,
            "image": image
        })

    return news_items

def extract_image(html_summary):
    soup = BeautifulSoup(html_summary, "html.parser")
    img = soup.find("img")
    return img["src"] if img and "src" in img.attrs else None

def clean_summary(summary_html):
    soup = BeautifulSoup(summary_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text[:500] + "..." if len(text) > 500 else text

def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%d %b %Y, %H:%M")
    except:
        return date_str
