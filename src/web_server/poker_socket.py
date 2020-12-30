import logging
from typing import Dict

from flask import request
from flask_socketio import join_room, leave_room

from database.repository import room_repository
from src.web_server import sio
from src.web_server.lib.game.Exceptions import PokerException
from src.web_server.lib.game.PokerTable import PokerTable
from src.web_server.lib.user_session import session_user

tables: Dict[int, PokerTable] = {}

print("Loaded socket functions")


@sio.on('join')
def on_join(data):
    room_id = int(data['room'])
    join_room(room=room_id)

    if room_id not in tables:
        tables[room_id] = PokerTable(room_id)

    profile = session_user()
    table = tables[room_id]
    table.add_player(profile, request.sid)

    sio.emit("join", profile.owner, json=True, room=room_id)
    table.update_players()


@sio.on('leave')
def on_leave(data):
    username = data['id']
    room_id = int(data['room'])
    leave_room(room_id)

    tables[room_id].broadcast("%s left the table." % username)
    sio.emit("leave", username, json=True, room=room_id)


@sio.on("chat message")
def message(data):
    room = int(data.get('room'))
    if message != "":  # Stop empty messages
        profile = session_user()
        data["username"] = profile.owner

        sio.emit('chat message', data, room=room, include_self=True)


@sio.on("start")
def start(data):
    room_id = int(data.get("room"))
    room = room_repository.get_room(room_id)
    profile = session_user()

    table = tables[room_id]
    player = table.get_player(profile)

    # All normal players toggle their ready state
    player.ready = not player.ready

    # Only the owner may start the game
    if room.author_id != profile.owner_id:
        print("Player state: ", player.ready)
        table.update_players()
        return

    # Room owner is always true
    player.ready = True
    if not table.check_readies():
        sio.emit("message", "The room owner wants to start. Ready up!", room=room_id)
        return

    try:
        table.initialize_round()
        table.update_players()

        # Assume everybody is ready, maybe implement ready check later
        sio.emit("start", None, room=room_id)
    except PokerException as e:
        print(e.message, player.socket)
        sio.emit("message", e.message, room=player.socket)


@sio.on("action")
def action(data):
    room_id = int(data.get("room"))

    table = tables[room_id]
    profile = session_user()

    player = table.get_player(profile)

    response = table.round(profile, data.get("action"), int(data.get("value", 0)))

    if response is not None:
        sio.emit("message", response, room=player.socket)

    for table_player in table.player_list:
        sio.emit("table_state", table.export_state(table_player), json=True, room=table_player.socket)


@sio.on("table_state")
def action(data):
    room_id = int(data.get("room"))

    table = tables[room_id]
    user = session_user()
    player = table.get_player(user)
    sio.emit("table_state", table.export_state(player), json=True, room=player.socket)


print("Loaded socket")
