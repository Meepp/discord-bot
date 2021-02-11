from datetime import datetime
from typing import Dict

from flask import request
from flask_socketio import join_room

from database.repository import room_repository
from database.repository.room_repository import get_room
from src.web_server import session_user, sio
from src.web_server.lib.game.HallwayHunters import HallwayHunters
from src.web_server.lib.game.PlayerClasses import PlayerClass
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.commands import handle_developer_command
from src.web_server.lib.game.exceptions import InvalidAction, InvalidCommand

games: Dict[int, HallwayHunters] = {}


@sio.on('ping', namespace="/hallway")
def ping():
    sio.emit("pong", room=request.sid, namespace="/hallway")


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
    if player is None:
        game.add_player(profile, request.sid)

    sio.emit("game_state", game.export_board(player), room=player.socket, namespace="/hallway")


@sio.on("start", namespace="/hallway")
def start_game(data):
    room_id = int(data.get("room"))
    selected_class = data.get("player_class")
    room = room_repository.get_room(room_id)
    profile = session_user()

    game = games[room_id]
    player = game.get_player(profile)

    # All normal players toggle their ready state
    player.ready = not player.ready

    # Update the player class if the user desired this
    if player.name != selected_class:
        cls = next((x for x in PlayerClass.__subclasses__() if x.__name__ == selected_class), None)
        if cls:
            player = player.convert_class(cls)
            game.set_player(profile, player)
            print("Updated player to:", player.name)

    # Only the owner may start the game
    if room.author_id != profile.discord_id:
        game.update_players()
        return

    # Room owner is always true
    player.ready = True

    if not game.game_loop_thread.is_alive():
        game.game_loop_thread.start()
    game.start()

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
    except InvalidAction as e:
        sio.emit("message", str(e.message), room=player.socket, namespace="/hallway")


@sio.on("action", namespace="/hallway")
def suggest_action(data):
    room_id = int(data.get("room"))
    action = data.get("action")
    game = games[room_id]

    profile = session_user()
    player = game.get_player(profile)

    try:
        if action == "c":
            player.ability()
        elif action == "x":
            player.sprint()
        elif action == "z":
            # Kill the first player in the list of visible players
            # TODO: Maybe a better method of selection
            player.kill()
    except InvalidAction as e:
        sio.emit("message", e.message, room=player.socket, namespace="/hallway")


@sio.on("chat message", namespace="/hallway")
def message(data):
    room_id = int(data.get('room'))
    room = room_repository.get_room(room_id)
    text_message = data.get('message')
    if text_message != "":  # Stop empty messages
        profile = session_user()
        data["username"] = profile.discord_username
        if text_message[0] == "/":
            data["profile"] = profile
            game = games[room_id]
            player = game.get_player(profile)
            try:
                handle_developer_command(data, game, room)
            except InvalidCommand as e:
                sio.emit('command error', e.message, room=player.socket, include_self=True, namespace="/hallway")
        else:

            sio.emit('chat message', data, room=room_id, include_self=True, namespace="/hallway")
