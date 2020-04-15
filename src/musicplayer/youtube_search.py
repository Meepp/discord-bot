import requests


class YoutubeAPI:
    def __init__(self, key):
        self.key = key

    def search(self, query):
        data = {
            "part": "id,snippet",
            "maxResults": 1,
            "q": query,
            "type": "video",
            "key": self.key
        }

        result = requests.get("https://www.googleapis.com/youtube/v3/search", params=data)
        return "https://www.youtube.com/watch?v=" + result.json()["items"][0]["id"]["videoId"]
