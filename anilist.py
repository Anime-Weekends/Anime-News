import aiohttp

API_URL = "https://graphql.anilist.co"

ANILIST_QUERY = """
query ($search: String, $type: MediaType) {
  Media(search: $search, type: $type) {
    id
    title {
      romaji
      english
      native
    }
    coverImage {
      large
    }
    description(asHtml: false)
    episodes
    chapters
    volumes
    status
    genres
    siteUrl
  }
}
"""

async def search_anilist(query: str, media_type: str = "ANIME") -> dict:
    variables = {
        "search": query,
        "type": media_type.upper()
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={"query": ANILIST_QUERY, "variables": variables}) as response:
            if response.status == 200:
                result = await response.json()
                return result["data"]["Media"] if "data" in result and "Media" in result["data"] else None
            else:
                return None
