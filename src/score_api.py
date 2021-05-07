import requests
import json

API_URL = "https://api.pandascore.co/lol/"
ACCESS_TOKEN = "5_Xi1C70nmyvwO7ymJG4HevgPlfu-uLBpZQSt-B0WSFuar4ALws"


def get_running_tournament_matches():
    matches = {}
    raw_response = requests.get(
        "https://api.pandascore.co/lol/tournaments/running?search[name]=group&token=" + ACCESS_TOKEN)
    if raw_response.status_code == 200:
        for group in raw_response.json():
            for match in group.get("matches"):
                matches[match.get("id")] = (match.get("name"), match.get("status"), match.get("winner_id"))
    return matches


def get_match_by_id(match_id):
    raw_response = requests.get(
        "https://api.pandascore.co/lol/matches?filter[id]=" + match_id + "&token=" + ACCESS_TOKEN)
    match = raw_response.json()[0]
    match_info = {"opponents": match.get("opponents"), "name": match.get("name"),
                  "winner": match.get("winner"), "status": match.get("games")[0].get("status"),
                  "league": match.get("league"),
                  "tournament": match.get("tournament")}

    return match_info


def is_game_finished(match_id: str):
    print(match_id)
    raw_response = requests.get(
        "https://api.pandascore.co/lol/matches?filter[id]=" + match_id + "&token=" + ACCESS_TOKEN)
    match = raw_response.json()[0]
    return match.get("games")[0].get("status")