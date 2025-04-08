import aiohttp

ANILIST_API = "https://graphql.anilist.co"

query = """
query ($search: String, $type: MediaType) {
  Media(search: $search, type: $type) {
    id
    title {
      romaji
      english
    }
    coverImage {
      large
    }
    siteUrl
    format
    status
    episodes
    chapters
    volumes
    duration
    description(asHtml: false)
  }
}
"""

async def search_anilist(name, media_type):
    async with aiohttp.ClientSession() as session:
        async with session.post(ANILIST_API, json={"query": query, "variables": {"search": name, "type": media_type}}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("data", {}).get("Media")
