import aiohttp

ANILIST_API = "https://graphql.anilist.co"

query = """
query ($search: String, $type: MediaType) {
  Media(search: $search, type: $type) {
    title {
      romaji
      english
    }
    description(asHtml: false)
    coverImage {
      large
    }
    siteUrl
  }
}
"""

async def search_anilist(name: str, media_type: str = "ANIME"):
    async with aiohttp.ClientSession() as session:
        payload = {"query": query, "variables": {"search": name, "type": media_type}}
        async with session.post(ANILIST_API, json=payload) as resp:
            data = await resp.json()
            return data.get("data", {}).get("Media")
