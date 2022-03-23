import copy
import random
import datetime
import threading
import time
from collections import defaultdict
from enum import Enum
from typing import List

from src.web_server import sio
from src.web_server.lib.capture.World import World

WORD_LISTS = defaultdict(list)


def filter_words(filename):
    valid_letters = "qwertyuiopasdfghjklzxcvbnm"

    def is_valid_word(word):
        for letter in word:
            if letter not in valid_letters:
                return False
        return True

    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not is_valid_word(line):
                continue

            WORD_LISTS[len(line)].append(line)


MIN_WORD_LENGTH = 2
MAX_WORD_LENGTH = 12
print("Initializing word lists.")
filter_words("storage/wordlist.txt")
print("Done initializing word lists.")


class CapturePhases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1
    FINISHED = 2


class CapturePlayer:
    def __init__(self, username, socket, table):
        self.username = username
        self.socket = socket
        self.table: CaptureGame = table
        self.ready = False

    def reset(self):
        ...

    def to_json(self):
        return {
            "name": self.username,
            "ready": self.ready,
        }


class CaptureGame:
    def __init__(self, room_id, author, word_length=6):
        self.config = {
            "room": room_id,
            "namespace": "/wordle"
        }
        self.room_id = room_id

        self.player_list: List[CapturePlayer] = []

        # The game room host.
        self.author = author
        self.world = World(n=7, random_factor=1, noise_factor=0.1)

    def initialize_round(self):
        """
        Initializes the current round, does not do full reinitialization of the room.
        :return:
        """
        for player in self.player_list:
            player.reset()

        self.broadcast_players()

        sio.emit("start", self.get_state(), **self.config)

    def get_state(self):
        return {
            "owner": self.author,
            "countries": self.world.country_areas,
        }

    def broadcast_players(self):
        sio.emit("players", [player.to_json() for player in self.player_list], json=True, **self.config)

    def join(self, player: CapturePlayer):
        self.player_list.append(player)

    def remove_player(self, player):
        self.player_list.remove(player)

    def get_player(self, username, socket_id=None):
        if socket_id is not None:
            for player in self.player_list:
                if player.socket == socket_id:
                    return player

        for player in self.player_list:
            if player.username == username:
                return player
        return None
