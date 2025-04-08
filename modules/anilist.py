import requests

def search_anilist(query, media_type="ANIME"):
    url = "https://graphql.anilist.co"
    query_string = '''
    query ($search: String, $type: MediaType) {
      Media(search: $search, type: $type) {
        title {
          romaji
          english
          native
        }
        description(asHtml: false)
        coverImage {
          large
        }
        siteUrl
      }
    }
    '''

    variables = {
        "search": query,
        "type": media_type.upper()
    }

    response = requests.post(url, json={"query": query_string, "variables": variables})
    if response.status_code == 200:
        data = response.json().get("data", {}).get("Media")
        return data
    return None
