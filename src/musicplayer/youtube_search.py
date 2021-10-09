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

        try:
            print("Request made to Youtube")
            result = requests.get("https://www.googleapis.com/youtube/v3/search", params=data)
            if result.status_code == 200:
                return "https://www.youtube.com/watch?v=" + result.json()["items"][0]["id"]["videoId"]
            else:
                raise ValueError("Was unable to find song")
        except ValueError as error:
            print(error)