import requests

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
                  "tournament": match.get("tournament"),
                  "scheduled_at": match.get("scheduled_at"),
                  "stream_url": match.get("official_stream_url")}

    return match_info


def is_game_finished(match_id: str):
    raw_response = requests.get(
        "https://api.pandascore.co/lol/matches?filter[id]=" + match_id + "&token=" + ACCESS_TOKEN)
    match = raw_response.json()[0]
    return match.get("games")[0].get("status")

def get_team_by_id(team_id: str):
    raw_response = requests.get(
        "https://api.pandascore.co/lol/teams?filter[id]=" + team_id + "&token=" + ACCESS_TOKEN)
    return raw_response.json()[0]


def get_team_by_acronym(acronym):
    raw_response = requests.get(
        "https://api.pandascore.co/lol/teams?search[acronym]=" + acronym + "&token=" + ACCESS_TOKEN)
    return raw_response.json()[-1]


def get_upcoming_matches():
    raw_response = requests.get(
        "https://api.pandascore.co/lol/matches/upcoming?page[size]=5&page[number]=1" + "&token=" + ACCESS_TOKEN)
    return raw_response.json()