import io
import threading

import discord
import requests

def main():
    data = {
        "part": "id,snippet",
        "maxResults": 1,
        "q": "miracle caravan palace",
        "key": "a"
    }

    result = requests.get("https://www.googleapis.com/youtube/v3/search", params=data)

    print(result.json()["items"][0]["id"]["videoId"])


if __name__ == "__main__":
    main()