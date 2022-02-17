import copy
import random
import datetime
import threading
import time
from enum import Enum
from typing import List

from src.web_server import sio

WORD_LISTS = {

}


def filter_words(filename, word_length=5):
    valid_letters = "qwertyuiopasdfghjklzxcvbnm"

    def is_valid_word(word):
        for letter in word:
            if letter not in valid_letters:
                return False
        return True

    valid_words = []
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not is_valid_word(line):
                continue

            if len(line) != word_length:
                continue

            valid_words.append(line)

    WORD_LISTS[word_length] = valid_words


print("Initializing word lists.")
filter_words("storage/en_words.txt")
print("Done initializing word lists.")


class WordlePhases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1
    FINISHED = 2


class WordlePlayer:
    def __init__(self, profile: dict, socket, table):
        self.profile = profile
        self.socket = socket
        self.table: WordleTable = table

        self.n_correct_answers = 0
        self.guessed_current = False
        self.points = 0

    def guessed(self, points):
        self.guessed_current = True
        self.n_correct_answers += 1
        self.points += points

    def to_json(self):
        return {
            "name": self.profile["owner"],
            "n_correct": self.n_correct_answers,
            "points": round(self.points, ndigits=1),
            "guessed": self.guessed_current,
        }


class WordleTable:
    MAX_ROUNDS = 20
    PLAYER_MULTIPLIER = 1.123
    SPEED_MULTIPLIER = 2.413

    def __init__(self, room_id, author, word_length=5):
        self.config = {
            "room": room_id,
            "namespace": "/wordle"
        }

        self.room_id = room_id

        self.player_list: List[WordlePlayer] = []
        self.valid_words = WORD_LISTS[word_length]
        self.word_list = random.sample(WORD_LISTS[word_length], self.MAX_ROUNDS)

        # The game room host.
        self.author = author

        self.current_word_index = 0
        self.current_guess_index = 0

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

    def initialize_round(self):
        """
        Initializes the current round, does not do full reinitialization of the room.
        :return:
        """

        for player in self.player_list:
            player.guessed_current = False

        self.ongoing = True

        self.broadcast_players()
        self.end_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
        sio.emit("start", self.get_state(), **self.config)

    def handle_round_end(self):
        """
        Checks if the round can end, and will start a new round if this is the case.
        :return:
        """
        if self.check_players_left():
            return False

        self.initialize_round()

    def get_state(self):
        return {
            "owner": self.author,
            "end_time": self.end_time.isoformat()
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

        # Cannot guess twice.
        if player.guessed_current:
            return

        if guessed_word not in self.valid_words:
            return

        current_word = self.word_list[self.current_word_index]

        if guessed_word == current_word:
            nth_guess_points = self.n_players_left() * self.PLAYER_MULTIPLIER
            time_points = (self.end_time - datetime.datetime.now()).total_seconds() * self.SPEED_MULTIPLIER
            player.guessed(nth_guess_points + time_points)
            self.broadcast_players()
            self.handle_round_end()
            return

        correct_position = []
        correct_character = []
        correct_word = [letter for letter in current_word]
        for idx, char in enumerate(guessed_word):
            if char == correct_word[idx]:
                correct_position.append(idx)
                correct_word[idx] = '_'

        for idx, char in enumerate(guessed_word):
            if char in correct_word:
                correct_character.append(idx)
                correct_word.remove(char)

        # If we send a response, the guess index goes up by one.
        self.current_guess_index += 1

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

    def get_player(self, profile):
        for player in self.player_list:
            if player.profile["owner_id"] == profile["owner_id"]:
                return player
        return None
