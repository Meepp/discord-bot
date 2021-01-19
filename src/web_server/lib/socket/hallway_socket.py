from typing import Dict

from flask import request
from flask_socketio import join_room

from database.repository import room_repository
from src.web_server import session_user, sio
from src.web_server.lib.game.HallwayHunters import HallwayHunters
from web_server.lib.game.Utils import Point
from web_server.lib.game.exceptions import InvalidAction

games: Dict[int, HallwayHunters] = {}


@sio.on("join", namespace="/hallway")
def on_join(data):
    room_id = int(data['room'])
    join_room(room=room_id)

    if room_id not in games:
        games[room_id] = HallwayHunters(room_id)

    profile = session_user()
    game = games[room_id]
    game.add_player(profile, request.sid)

    sio.emit("join", profile.discord_username, json=True, room=room_id, namespace="/hallway")
    game.update_players()


@sio.event(namespace="/hallway")
def disconnect():
    for room_id, game in games.items():
        player = game.get_player(socket_id=request.sid)
        if player:
            game.remove_player(player.profile)

            game.broadcast("%s left the game." % player.profile.discord_username)
            sio.emit("leave", player.profile.discord_username, json=True, room=room_id, namespace="/hallway")


@sio.on("game_state", namespace="/hallway")
def get_state(data):
    room_id = int(data['room'])

    game = games[room_id]

    profile = session_user()
    player = game.get_player(profile=profile)
    sio.emit("game_state", game.export_board(player), room=player.socket, namespace="/hallway")


@sio.on("start", namespace="/hallway")
def start_game(data):
    room_id = int(data.get("room"))
    room = room_repository.get_room(room_id)
    profile = session_user()

    game = games[room_id]
    player = game.get_player(profile)

    # All normal players toggle their ready state
    player.ready = not player.ready

    # Only the owner may start the game
    if room.author_id != profile.discord_id:
        game.update_players()
        return

    # Room owner is always true
    player.ready = True
    if not game.check_readies():
        sio.emit("message", "The room owner wants to start. Ready up!", room=room_id, namespace="/hallway")
        return

    game.update_players()

    sio.emit("start", None, room=room_id, namespace="/hallway")


@sio.on("move", namespace="/hallway")
def suggest_move(data):
    room_id = int(data.get("room"))
    game = games[room_id]

    profile = session_user()

    player = game.get_player(profile)

    move = data.get("move")
    position = Point(move.get("x"), move.get("y"))

    try:
        player.suggest_move(position)
        game.update_players()
    except InvalidAction as e:
        sio.emit("message", e.message, room=player.socket, namespace="/hallway")
