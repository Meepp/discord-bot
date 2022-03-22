import copy
import random
import datetime
import threading
import time
from collections import defaultdict
from enum import Enum
from typing import List

from src.web_server import sio

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


class WordlePhases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1
    FINISHED = 2


class WordlePlayer:
    def __init__(self, username, socket, table):
        self.username = username
        self.socket = socket
        self.table: WordleTable = table

        self.n_correct_answers = 0
        self.guessed_current = False
        self.points = 0
        self.ready = False

    def guessed(self, points):
        self.guessed_current = True
        self.n_correct_answers += 1
        self.points += points

    def reset(self):
        self.guessed_current = False

    def to_json(self):
        return {
            "name": self.username,
            "n_correct": self.n_correct_answers,
            "points": round(self.points, ndigits=1),
            "guessed": self.guessed_current,
            "ready": self.ready,
        }


class WordleTable:
    MAX_ROUNDS = 20
    PLAYER_MULTIPLIER = 1.123
    SPEED_MULTIPLIER = 2.413

    def __init__(self, room_id, author, word_length=6):
        self.config = {
            "room": room_id,
            "namespace": "/wordle"
        }
        self.word_length = word_length
        self.room_id = room_id

        self.player_list: List[WordlePlayer] = []
        self.current_word = ""

        self.guessed_words = []

        # The game room host.
        self.author = author

        self.round = 0

        self.end_time = datetime.datetime.now()

        self.timer_thread = threading.Thread(target=self.check_end)
        self.timer_thread.start()

        self.ongoing = False

    def check_end(self):
        while True:
            time.sleep(1)
            if not self.ongoing:
                continue
            if self.end_time < datetime.datetime.now():
                self.ongoing = False

                response = {
                    "player": None,
                    "word": self.current_word, "correct_position": [],
                    "correct_character": []
                }
                sio.emit("word", response, json=True, **self.config)

    def initialize_round(self):
        """
        Initializes the current round, does not do full reinitialization of the room.
        :return:
        """
        for player in self.player_list:
            player.reset()

        self.broadcast_players()

        self.round += 1

        self.word_length = random.randint(MIN_WORD_LENGTH, MAX_WORD_LENGTH)

        self.ongoing = True
        self.guessed_words = []
        self.current_word = random.sample(WORD_LISTS[self.word_length], 1)[0]

        seconds = (60 + max(0, self.word_length - 5) * 30)
        self.end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        sio.emit("start", self.get_state(), **self.config)

    def handle_round_end(self):
        """
        Checks if the round can end, and will start a new round if this is the case.
        :return:
        """
        if len(self.guessed_words) == 10 or not self.check_players_left():
            response = {
                "player": None,
                "word": self.current_word, "correct_position": [],
                "correct_character": []
            }
            sio.emit("word", response, json=True, **self.config)
            self.ongoing = False

    def get_state(self):
        return {
            "owner": self.author,
            "end_time": self.end_time.isoformat(),
            "word_length": self.word_length,
        }

    def n_players_left(self):
        n = 0
        for player in self.player_list:
            # If they didnt guess yet, they are still playing.
            n += (not player.guessed_current)

        return n

    def check_players_left(self):
        for player in self.player_list:
            if not player.guessed_current:
                return True
        return False

    def check_word(self, player: WordlePlayer, guessed_word: str):
        # Cannot guess if game is not ongoing (time ran out)
        if not self.ongoing:
            return

        # Cannot guess a word which was already guessed this round.
        if guessed_word in self.guessed_words:
            return

        # Cannot guess twice.
        if player.guessed_current:
            return

        if guessed_word not in WORD_LISTS[self.word_length]:
            return

        if guessed_word == self.current_word:
            nth_guess_points = self.n_players_left() * self.PLAYER_MULTIPLIER
            time_points = (self.end_time - datetime.datetime.now()).total_seconds() * self.SPEED_MULTIPLIER
            player.guessed(nth_guess_points + time_points)

            sio.emit("correct", room=player.socket, namespace="/wordle")

            self.broadcast_players()
            self.handle_round_end()
            return

        correct_position = []
        correct_character = []
        correct_word = [letter for letter in self.current_word]
        for idx, char in enumerate(guessed_word):
            if char == correct_word[idx]:
                correct_position.append(idx)
                correct_word[idx] = '_'

        for idx, char in enumerate(guessed_word):
            if char in correct_word:
                correct_character.append(idx)
                correct_word.remove(char)

        self.guessed_words.append(guessed_word)
        response = {
            "player": player.to_json(),
            "word": guessed_word, "correct_position": correct_position,
            "correct_character": correct_character
        }
        sio.emit("word", response, json=True, **self.config)

        # We have to check for round end, this could be the last possible word choice.
        self.handle_round_end()

    def broadcast_players(self):
        sio.emit("players", [player.to_json() for player in self.player_list], json=True, **self.config)

    def join(self, player: WordlePlayer):

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
