# rss.py

import feedparser
import html
import requests
from bs4 import BeautifulSoup

def fetch_news(feed_url, limit=3):
    parsed = feedparser.parse(feed_url)
    entries = parsed.entries[:limit]
    news_list = []

    for entry in entries:
        title = html.unescape(entry.get("title", "No Title"))
        link = entry.get("link", "")
        summary = html.unescape(entry.get("summary", ""))
        published = entry.get("published", "No date")

        image_url = extract_image_from_summary(summary) or extract_image_from_page(link)

        clean_summary = clean_html(summary)
        text = f"**{title}**\n\n{clean_summary}\n\n**Published:** `{published}`"

        news_list.append({
            "title": title,
            "link": link,
            "summary": clean_summary,
            "published": published,
            "text": text,
            "image": image_url
        })

    return news_list

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text()
    return text.strip()[:1000] + "..." if len(text) > 1000 else text

def extract_image_from_summary(summary):
    soup = BeautifulSoup(summary, "html.parser")
    img = soup.find("img")
    return img["src"] if img else None

def extract_image_from_page(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "html.parser")
        meta_img = soup.find("meta", property="og:image")
        return meta_img["content"] if meta_img else None
    except:
        return None
