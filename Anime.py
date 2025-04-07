import json
from calendar import month_name
import aiohttp
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_readable_time(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours}h")
    if minutes > 0:
        time_parts.append(f"{minutes}m")
    if sec > 0:
        time_parts.append(f"{sec}s")
    return " ".join(time_parts)

media_query = """
query ($id: Int, $idMal: Int, $search: String, $type: MediaType) {
  Media(id: $id, idMal: $idMal, type: $type, search: $search) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: true)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    tags {
      name
      description
      rank
    }
    relations {
      edges {
        node {
          id
          title {
            romaji
            english
            native
          }
          format
          status
          source
          averageScore
          siteUrl
        }
        relationType
      }
    }
    characters {
      edges {
        role
        node {
          name {
            full
            native
          }
          siteUrl
        }
      }
    }
    studios {
      nodes {
         name
         siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    rankings {
      rank
      year
      context
    }
    reviews {
      nodes {
        summary
        rating
        score
        siteUrl
        user {
          name
        }
      }
    }
    siteUrl
  }
}
"""

async def get_media(variables):
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://graphql.anilist.co",
            json={"query": media_query, "variables": variables}
        )
        return await response.read()

def shorten(description, info="anilist.co"):
    ms_g = ""
    if len(description) > 700:
        description = f"{description[:500]}...."
        ms_g += f'\n<strong>Description:</strong> <em>{description}</em><a href="{info}">More info</a>'
    else:
        ms_g += f"\n<strong>Description:</strong> <em>{description}</em>"
    return (
        ms_g.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )

async def handle_media(mesg, media_type):
    search = mesg.text.split(None, 1)
    reply = await mesg.reply("⏳ <i>Please wait ...</i>", quote=True)
    if len(search) == 1:
        return await reply.edit(f"⚠️ <b>Give {media_type.capitalize()} name please.</b>")
    search = search[1]
    variables = {"search": search, "type": media_type.upper()}
    data = json.loads(await get_media(variables))["data"]
    res = data.get("Media", None)
    if not res:
        return await reply.edit("💢 No Resource found! [404]")

    msg = f"<b>{res['title']['romaji']}</b> (<code>{res['title']['native']}</code>)\n<b>Type</b>: {res['format']}\n<b>Status</b>: {res['status']}\n"
    
    if media_type == "anime":
        durasi = get_readable_time(int(res.get("duration", 0) * 60))
        msg += f"<b>Episodes</b>: {res.get('episodes', 'N/A')}\n<b>Duration </b>: {durasi} Per Eps.\n"
    else:
        msg += f"<b>Chapters</b>: {res.get('chapters', 'N/A')}\n<b>Volumes</b>: {res.get('volumes', 'N/A')}\n"

    msg += f"<b>Score</b>: {res.get('averageScore', 'N/A')}%\n<b>Category</b>: <code>"
    for genre in res.get("genres", []):
        msg += f"{genre}, "
    msg = msg.rstrip(", ") + "</code>\n"

    try:
        sd = res["startDate"]
        startdate = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}"
    except:
        startdate = "-"
    msg += f"<b>Start date</b>: <code>{startdate}</code>\n"

    try:
        ed = res["endDate"]
        enddate = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}"
    except:
        enddate = "-"
    msg += f"<b>End date</b>: <code>{enddate}</code>\n"

    msg += "<b>Studios</b>: <code>"
    for studio in res.get("studios", {}).get("nodes", []):
        msg += f"{studio['name']}, "
    msg = msg.rstrip(", ") + "</code>\n"

    info = res.get("siteUrl")
    trailer = res.get("trailer")
    trailer_url = None
    if trailer and trailer.get("site") == "youtube":
        trailer_url = f"https://youtu.be/{trailer['id']}"

    description = res.get("description", "N/A")
    msg += shorten(description, info)

    image = info.replace("anilist.co/anime/", "img.anili.st/media/") if "anime" in info else res["coverImage"]["large"]
    btn = [[InlineKeyboardButton("More info", url=info)]]
    if trailer_url:
        btn[0].append(InlineKeyboardButton("Trailer 🎬", url=trailer_url))

    try:
        await mesg.reply_photo(image, caption=msg, reply_markup=InlineKeyboardMarkup(btn))
        await reply.delete()
    except:
        msg += f"\n[Image]({image})"
        await reply.edit(msg)

@Client.on_message(filters.command("anime", "/"))
async def anime_handler(client, message):
    await handle_media(message, "anime")

@Client.on_message(filters.command("manga", "/"))
async def manga_handler(client, message):
    await handle_media(message, "manga")
