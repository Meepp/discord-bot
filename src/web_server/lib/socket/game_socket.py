from typing import Dict

from flask import request

from web_server import session_user, sio
from web_server.lib.game.Game import Game

games: Dict[int, Game] = {}


def join_game(room_id):
    if room_id not in games:
        games[room_id] = Game(room_id)

    profile = session_user()
    table = games[room_id]
    table.add_player(profile, request.sid)

    sio.emit("join", profile.owner, json=True, room=room_id)
    table.update_players()


def leave_game(socket_id):
    for room_id, game in games.items():
        player = game.get_player(socket_id=socket_id)
        if player:
            game.remove_player(player.profile)

            game.broadcast("%s left the game." % player.profile.owner)
            sio.emit("leave", player.profile.owner, json=True, room=room_id)
