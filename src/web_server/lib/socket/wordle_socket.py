from typing import Dict

import socketio
from flask import request

from database.repository import room_repository
from src.web_server import session_user, sio
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.commands import handle_developer_command
from src.web_server.lib.game.exceptions import InvalidAction, InvalidCommand
from web_server.lib.wordle import WordleTable
from web_server.lib.wordle.WordleTable import WordlePhases

tables: Dict[int, WordleTable] = {}


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
        room_id = data.get("room")

        room = room_repository.get_room(room_id)
        profile = session_user()

        table = tables[room_id]
        player = table.get_player(profile)

        player.ready = not player.ready

        if room['author_id'] != profile['owner_id']:
            table.update_players()
            return

        player.ready = True
        if not table.check_readies():
            sio.emit("message", "The room owner wants to start. Ready up!", room=room_id, namespace="/poker")
            return
        if table.phase != WordlePhases.NOT_YET_STARTED:
            return
        try:
            table.initialize_round()
            sio.emit("start", None, room=room_id)
        except:
            print("Something went wrong.")

    @staticmethod
    def on_word(data):
        room_id = int(data.get("room"))
        profile = session_user()
        table = tables[room_id]
        guessed_word = data.get("word")
        player = table.get_player(profile)

        response = table.check_word(player, guessed_word)

        if response is not None:
            sio.emit("word", response, room=player.socket)


