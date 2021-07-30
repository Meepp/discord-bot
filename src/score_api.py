import requests
from PIL import Image
import discord
from discord.ext.commands import BadArgument

API_URL = "https://api.pandascore.co/lol/"


def get_match_image(opponents):
    image1 = convert_image(opponents[0]["opponent"].get("image_url"))

    image2 = convert_image(opponents[1]["opponent"].get("image_url"))

    padding = 10

    width, height = image1.size[0], image1.size[1]
    new_image = Image.new('RGB', (2 * (width + padding * 2), height + padding * 2), (47, 49, 54))
    new_image.paste(image1, (padding, padding))
    new_image.paste(image2, (width + padding * 3, padding))
    new_image.save('match_image.png', "PNG")
    file = discord.File("match_image.png", filename="match_image.png")

    return file


def convert_image(image_url):
    image1 = Image.open(requests.get(image_url, stream=True).raw)
    image1 = image1.resize((200, 200))
    bg_image1 = Image.new("RGB", image1.size, (47, 49, 54))
    bg_image1.paste(image1, mask=image1.split()[3])  # 3 is the alpha channel
    return bg_image1


class PandaScoreAPI:
    def __init__(self, key):
        self.key = key

    def league_id_from_name(self, name):
        json_response = requests.get(f"{API_URL}/leagues?filter[name]={name}&token={self.key}").json()
        for entry in json_response:
            return entry.get("id")
        return None

    def get_ongoing_match(self, league):
        league_id = self.league_id_from_name(league)
        if league_id is None:
            raise BadArgument("No leagues found with that name.")
        raw_response = requests.get(
            f"{API_URL}/matches/running?filter[league_id]={league_id}&token={self.key}")
        if raw_response.status_code == 200:
            if not raw_response.json():
                return
            ongoing_match = raw_response.json()[0]
            return int(ongoing_match.get("id"))

    def get_match_by_id(self, match_id):
        raw_response = requests.get(
            f"{API_URL}/matches?filter[id]={match_id}&token={self.key}")
        if raw_response.status_code != 200:
            return None
        if len(raw_response.json()) == 0:
            return None
        match = raw_response.json()[0]
        image_file = get_match_image(match.get("opponents"))
        match_info = {"opponents": match.get("opponents"), "name": match.get("name"),
                      "winner": match.get("winner"), "status": match.get("games")[0].get("status"),
                      "league": match.get("league"),
                      "tournament": match.get("tournament"),
                      "scheduled_at": match.get("scheduled_at"),
                      "stream_url": match.get("official_stream_url"),
                      "image_file": image_file}

        return match_info

    def is_game_finished(self, match_id: str):
        raw_response = requests.get(
            f"{API_URL}/matches?filter[id]={match_id}&token={self.key}")
        match = raw_response.json()[0]
        return match.get("games")[0].get("status")

    def get_team_by_id(self, team_id: str):
        raw_response = requests.get(
            f"{API_URL}/teams?filter[id]={team_id}&token={self.key}")
        return raw_response.json()

    def get_team_by_acronym(self, acronym):
        raw_response = requests.get(
            f"{API_URL}/teams?search[acronym]={acronym}&token={self.key}")

        return list(filter(lambda x: len(x.get("players")) >= 5, raw_response.json()))

    def get_upcoming_matches(self, league):
        if league is None:
            raw_response = requests.get(
                f"{API_URL}/matches/upcoming?page[size]=5&page[number]=1&token={self.key}")
        else:
            league_id = self.league_id_from_name(league)
            if league_id is None:
                raise BadArgument("No leagues found with that name.")
            raw_response = requests.get(
                f"{API_URL}/matches/upcoming?"
                f"filter[league_id]={league_id}&page[size]=5&page[number]=1&token={self.key}")
        return raw_response.json()
