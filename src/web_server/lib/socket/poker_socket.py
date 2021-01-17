import logging
from typing import Dict

from flask import request
from flask_socketio import join_room, leave_room

from database.repository import room_repository
from src.web_server import sio
from src.web_server.lib.poker.exceptions import PokerException
from src.web_server.lib.poker.PokerTable import PokerTable
from src.web_server.lib.user_session import session_user
from web_server.lib.poker.PokerSettings import PokerSettings

tables: Dict[int, PokerTable] = {}


def join_poker(room_id):
    if room_id not in tables:
        tables[room_id] = PokerTable(room_id)

    profile = session_user()
    table = tables[room_id]
    table.add_player(profile, request.sid)

    sio.emit("join", profile.owner, json=True, room=room_id)
    table.update_players()


def leave_poker(socket_id):
    for room_id, table in tables.items():
        player = table.get_player(socket_id=socket_id)
        if player:
            table.remove_player(player.profile)

            table.broadcast("%s left the table." % player.profile.owner)
            sio.emit("leave", player.profile.owner, json=True, room=room_id)


@sio.on("chat message")
def message(data):
    room = int(data.get('room'))
    if message != "":  # Stop empty messages
        profile = session_user()
        data["username"] = profile.owner

        sio.emit('chat message', data, room=room, include_self=True)


@sio.on("change settings")
def change_settings(data):
    print("Change settings")

    room_id = int(data.get("room_id"))
    room = room_repository.get_room(room_id)
    table = tables[room_id]
    profile = session_user()
    
    # Only the owner may change room settings
    if room.author_id != profile.owner_id:
        user = table.get_player(profile)
        return sio.emit("message", "You may not change the room settings.", room=user.socket)

    table.settings = PokerSettings(data.get("settings", {}))
    table.update_players()


@sio.on("start")
def start(data):
    print("Received start")

    room_id = int(data.get("room"))
    room = room_repository.get_room(room_id)
    profile = session_user()

    table = tables[room_id]
    player = table.get_player(profile)

    # All normal players toggle their ready state
    player.ready = not player.ready

    # Only the owner may start the game
    if room.author_id != profile.owner_id:
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
        sio.emit("message", e.message, room=player.socket)


@sio.on("action")
def action(data):
    print("Received action")
    room_id = int(data.get("room"))

    table = tables[room_id]
    profile = session_user()

    player = table.get_player(profile)
    if player is None:
        player = table.get_player(profile, spectator=True)
        return sio.emit("message", "You are currently spectating.", room=player.socket)

    response = table.round(profile, data.get("action"), int(data.get("value", 0)))

    if response is not None:
        sio.emit("message", response, room=player.socket)

    for table_player in table.player_list + table.spectator_list:
        sio.emit("table_state", table.export_state(table_player), json=True, room=table_player.socket)


@sio.on("table_state")
def action(data):
    print("Received table request")

    room_id = int(data.get("room"))

    table = tables[room_id]
    user = session_user()
    player = table.get_player(user, spectator=True)
    if not player:
        return
    sio.emit("table_state", table.export_state(player), json=True, room=player.socket)


print("Loaded socket")
