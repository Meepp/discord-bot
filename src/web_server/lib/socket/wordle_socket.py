import logging
from functools import wraps
from time import time
from typing import Dict

import socketio
from flask import request
from flask_socketio import join_room

from database.repository import room_repository
from src.web_server import session_user, sio
from web_server.lib.wordle.WordleTable import WordlePhases, WordleTable, WordlePlayer

tables: Dict[int, WordleTable] = {}


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger = logging.getLogger("timing")
        logger.info(f"{f.__name__}: {te - ts}")
        return result
    return wrap


@sio.on("ping", namespace="/wordle")
def on_ping():
    sio.emit("pong", room=request.sid, namespace="/wordle")


@sio.on("start", namespace="/wordle")
@timing
def on_start(data):
    room_id = int(data.get("room"))

    profile = session_user()

    room = room_repository.get_room(room_id)

    table = tables[room_id]

    if room['author_id'] != profile['owner_id']:
        return

    table.initialize_round()


@sio.on("join", namespace="/wordle")
@timing
def on_join(data):
    room_id = int(data.get("room"))
    join_room(room_id)

    # Initialize table if this hasn't been done yet.
    room = room_repository.get_room(room_id)
    if room_id not in tables:
        tables[room_id] = WordleTable(room_id, author=room["author_id"])

    if tables[room_id].get_player(session_user()):
        return

    sio.emit("join", "message", json=True, room=room_id, namespace="/wordle")
    # Initialize player and add to table, then inform other players
    player = WordlePlayer(session_user(), request.sid, tables[room_id])
    tables[room_id].join(player)
    tables[room_id].broadcast_players()


@sio.on("word", namespace="/wordle")
@timing
def on_word(data):
    room_id = int(data.get("room"))
    guessed_word = data.get("word")

    table = tables[room_id]

    # Check if player is in this room
    profile = session_user()
    player = table.get_player(profile)
    if not player:
        print(f"{player} tried to send a word.")
        return

    response = table.check_word(player, guessed_word)
