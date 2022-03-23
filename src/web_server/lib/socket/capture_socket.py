from typing import Dict

from flask import request
from flask_socketio import join_room

from src.web_server import session_user, sio, timing
from src.web_server.lib.capture.CaptureGame import CaptureGame, CapturePlayer
from src.web_server.lib.user_session import session_user_set

tables: Dict[int, CaptureGame] = {}


@sio.event(namespace="/capture")
@timing
def disconnect():
    to_remove_ids = []
    for room_id, game in tables.items():
        player = game.get_player(None, socket_id=request.sid)
        if player:
            game.remove_player(player)
            game.broadcast_players()
            if len(game.player_list) == 0:
                to_remove_ids.append(room_id)

    for remove_id in to_remove_ids:
        print(f"Empty room {remove_id}, deleting.")
        del tables[remove_id]


@sio.on("ping", namespace="/capture")
def on_ping():
    sio.emit("pong", room=request.sid, namespace="/capture")


@sio.on("start", namespace="/capture")
@timing
def on_start(data):
    room_id = int(data.get("room"))

    table = tables[room_id]

    # Check if any player is not ready, if so, you cant start yet.
    for player in table.player_list:
        if player.ready is False:
            return

    table.initialize_round()


@sio.on("set_session", namespace="/capture")
@timing
def on_set_session(data):
    username = data.get("username", None)
    print(f"{username} connected.")
    if session_user() is None:
        session_user_set(username)

    sio.emit("set_session", username, room=request.sid, namespace="/capture")


@sio.on("join", namespace="/capture")
@timing
def on_join(data):
    room_id = int(data.get("room"))

    join_room(room_id)

    username = session_user()
    # Initialize table if this hasn't been done yet.
    if room_id not in tables:
        tables[room_id] = CaptureGame(room_id, author=username)

    table = tables[room_id]

    # Add new player to table if it is not already in there.
    if not table.get_player(session_user()):
        sio.emit("join", "message", json=True, room=room_id, namespace="/capture")
        # Initialize player and add to table, then inform other players
        player = CapturePlayer(username, request.sid, table)
        table.join(player)

    table.broadcast_players()


@sio.on("ready", namespace="/capture")
@timing
def on_ready(data):
    room_id = int(data.get("room"))
    table = tables[room_id]
    player = table.get_player(session_user())
    player.ready = True
    table.broadcast_players()

