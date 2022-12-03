from typing import Dict

from flask import request
from flask_socketio import join_room

from src.web_server import session_user, sio, timing
from src.web_server.lib.game.HallwayHunters import HallwayHunters, Phases
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.commands import handle_developer_command
from src.web_server.lib.game.exceptions import InvalidAction, InvalidCommand
from web_server.lib.game.PlayerClasses import PlayerState
from web_server.lib.user_session import session_user_set

games: Dict[int, HallwayHunters] = {}


@sio.on('ping', namespace="/hallway")
@timing
def ping():
    sio.emit("pong", room=request.sid, namespace="/hallway")


@sio.on("set_session", namespace="/hallway")
@timing
def on_set_session(data):
    username = data.get("username", None)
    print(f"{username} connected.")
    if session_user() is None:
        session_user_set(username)

    sio.emit("set_session", username, room=request.sid, namespace="/hallway")


@sio.on("join", namespace="/hallway")
@timing
def on_join(data):
    room_id = int(data['room'])
    join_room(room=room_id)
    username = session_user()

    if room_id not in games:
        games[room_id] = HallwayHunters(room_id, username)

    game = games[room_id]
    game.add_player(username, request.sid)

    sio.emit("join", username, json=True, room=room_id, namespace="/hallway")
    game.update_players()


@sio.event(namespace="/hallway")
@timing
def disconnect():
    for room_id, game in games.items():
        print("Looking for disconnect...")
        player = game.get_player(socket_id=request.sid)
        if player:
            print("Found player!")
            game.remove_player(player.username)

            game.broadcast("%s left the game." % player.username)
            sio.emit("leave", player.username, json=True, room=room_id, namespace="/hallway")


@sio.on("game_state", namespace="/hallway")
@timing
def get_state(data):
    room_id = int(data['room'])

    game = games[room_id]

    username = session_user()
    player = game.get_player(username=username)
    if player is None:
        player = game.add_player(username, request.sid)

    sio.emit("game_state", game.export_board(player), room=player.socket, namespace="/hallway")


@sio.on("start", namespace="/hallway")
@timing
def start_game(data):
    room_id = int(data.get("room"))
    username = session_user()

    game = games[room_id]

    # Only the owner may start the game
    if game.author != username:
        game.update_players()
        return

    sio.emit("loading", "Generating game...", room=room_id, namespace="/hallway")
    if not game.game_loop_thread.is_alive():
        game.game_loop_thread.start()

    game.start()

    sio.emit("start", None, room=room_id, namespace="/hallway")


@sio.on("changeColor", namespace="/hallway")
@timing
def change_color(data):
    room_id = int(data.get("room_id"))
    color = data.get("color")
    game = games[room_id]

    username = session_user()
    game.set_color(username, color)

    game.update_players()


@sio.on("action", namespace="/hallway")
@timing
def suggest_action(data):
    room_id = int(data.get("room"))
    action = data.get("action")
    game = games[room_id]
    if game.phase == Phases.NOT_YET_STARTED:
        return
    username = session_user()
    player = game.get_player(username)

    try:
        player.prepare_action(action, data.get("extra", None))
    except InvalidAction as e:
        sio.emit("message", e.message, room=player.socket, namespace="/hallway")


@sio.on("chat message", namespace="/hallway")
@timing
def message(data):
    room_id = int(data.get('room'))
    text_message = data.get('message')
    if text_message != "":  # Stop empty messages
        username = session_user()
        data["username"] = username
        if text_message[0] == "/":
            game = games[room_id]
            player = game.get_player(username)
            try:
                handle_developer_command(data, game)
            except InvalidCommand as e:
                sio.emit('command error', e.message, room=player.socket, include_self=True, namespace="/hallway")
        else:

            sio.emit('chat message', data, room=room_id, include_self=True, namespace="/hallway")
