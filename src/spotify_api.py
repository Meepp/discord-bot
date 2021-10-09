import requests

from discord import User
from discord.ext import commands, tasks
from discord.ext.commands import Context

client_id = '7387e3e128ba46caa345701f36489d8f'
client_secret = '4c618187275245beb795f9312e1f0d58'


import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri="http://localhost:8080/",
                                               scope="user-read-currently-playing"))

results = sp.current_user_playing_track()
print()
# for idx, item in enumerate(results['items']):
#     track = item['track']
#     print(idx, track['artists'][0]['name'], " – ", track['name'])


# https://api.spotify.com/v1/me/player/currently-playing?market=ES&additional_types=episode