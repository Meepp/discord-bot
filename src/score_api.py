import requests
from PIL import Image
import discord
API_URL = "https://api.pandascore.co/lol/"


def get_match_image(opponents):
    image1 = Image.open(requests.get(opponents[0]["opponent"].get("image_url"), stream=True).raw)
    image2 = Image.open(requests.get(opponents[1]["opponent"].get("image_url"), stream=True).raw)

    new_image = Image.new('RGB',(2*image1.size[0], image1.size[1]), (250,250,250))
    new_image.paste(image1,(0,0))
    new_image.paste(image2,(image1.size[0],0))
    new_image.save('match_image.png', "PNG")
    file = discord.File("match_image.png", filename="match_image.png")

    return file

class PandaScoreAPI:
    def __init__(self, key):
        self.key = key

    def get_running_tournament_matches(self):
        matches = {}
        raw_response = requests.get(
            f"{API_URL}tournaments/running?search[name]=group&token=" + self.key)
        if raw_response.status_code == 200:
            for group in raw_response.json():
                for match in group.get("matches"):
                    matches[match.get("id")] = (match.get("name"), match.get("status"), match.get("winner_id"))
        return matches

    def get_match_by_id(self, match_id):
        raw_response = requests.get(
            f"{API_URL}matches?filter[id]=" + match_id + "&token=" + self.key)
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
            f"{API_URL}matches?filter[id]=" + match_id + "&token=" + self.key)
        match = raw_response.json()[0]
        return match.get("games")[0].get("status")

    def get_team_by_id(self, team_id: str):
        raw_response = requests.get(
            f"{API_URL}teams?filter[id]=" + team_id + "&token=" + self.key)
        return raw_response.json()


    def get_team_by_acronym(self, acronym):
        raw_response = requests.get(
            f"{API_URL}teams?search[acronym]=" + acronym + "&token=" + self.key)
        return raw_response.json()

    def get_upcoming_matches(self):
        raw_response = requests.get(
            f"{API_URL}matches/upcoming?page[size]=5&page[number]=1" + "&token=" + self.key)
        return raw_response.json()
