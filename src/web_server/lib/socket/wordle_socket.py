from typing import Dict

import socketio
from flask import request

from database.repository import room_repository
from src.web_server import session_user, sio
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.commands import handle_developer_command
from src.web_server.lib.game.exceptions import InvalidAction, InvalidCommand


class WordleSocket(socketio.ClientNamespace):
    @staticmethod
    def on_ping():
        sio.emit("pong", room=request.sid)

    @staticmethod
    def on_join(data):
        # TODO: Initialize game, maybe do something with init data
        room_id = 0

        sio.emit("join", "message", json=True, room=room_id)

    @staticmethod
    def on_start(data):
        ...
        # TODO: Game start logic.
        room_id = 0

        sio.emit("start", None, room=room_id)

    @staticmethod
    def on_word(data):
        ...
        # TODO: On receive word
        room_id = 0

        sio.emit("word", None, room=room_id)

