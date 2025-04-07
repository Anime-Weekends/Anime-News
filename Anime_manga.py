# anime_manga.py

import requests
from bs4 import BeautifulSoup

def get_anime_info(query):
    search_url = f"https://myanimelist.net/anime.php?q={query}"
    r = requests.get(search_url)
    soup = BeautifulSoup(r.content, "html.parser")
    first_result = soup.select_one("div.js-categories-seasonal.js-block-list.list")
    
    if not first_result:
        return None

    first_link = first_result.select_one("a")
    if not first_link:
        return None

    anime_url = first_link['href']
    anime_page = requests.get(anime_url)
    anime_soup = BeautifulSoup(anime_page.content, "html.parser")

    title = anime_soup.select_one("h1.title-name strong").text.strip()
    image = anime_soup.select_one("img.ac")["data-src"]
    synopsis = anime_soup.select_one("p[itemprop='description']")
    synopsis = synopsis.text.strip().replace("\n", "") if synopsis else "No description."

    info_rows = anime_soup.select("div.spaceit_pad")
    info = ""
    for row in info_rows:
        text = row.text.strip()
        if any(k in text for k in ["Type:", "Episodes:", "Status:", "Aired:", "Score:", "Genres:", "Rating:"]):
            info += f"{text}\n"

    return {
        "url": anime_url,
        "image": image,
        "caption": f"**{title}**\n\n{synopsis}\n\n{info}",
    }


def get_manga_info(query):
    search_url = f"https://myanimelist.net/manga.php?q={query}"
    r = requests.get(search_url)
    soup = BeautifulSoup(r.content, "html.parser")
    first_result = soup.select_one("div.js-categories-seasonal.js-block-list.list")

    if not first_result:
        return None

    first_link = first_result.select_one("a")
    if not first_link:
        return None

    manga_url = first_link['href']
    manga_page = requests.get(manga_url)
    manga_soup = BeautifulSoup(manga_page.content, "html.parser")

    title = manga_soup.select_one("h1.title-name strong").text.strip()
    image = manga_soup.select_one("img.ac")["data-src"]
    synopsis = manga_soup.select_one("p[itemprop='description']")
    synopsis = synopsis.text.strip().replace("\n", "") if synopsis else "No description."

    info_rows = manga_soup.select("div.spaceit_pad")
    info = ""
    for row in info_rows:
        text = row.text.strip()
        if any(k in text for k in ["Type:", "Volumes:", "Status:", "Published:", "Score:", "Genres:", "Serialization:"]):
            info += f"{text}\n"

    return {
        "url": manga_url,
        "image": image,
        "caption": f"**{title}**\n\n{synopsis}\n\n{info}",
    }
