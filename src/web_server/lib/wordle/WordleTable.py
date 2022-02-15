from typing import List

from enum import Enum

import random


class WordlePhases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1
    FINISHED = 2


class WordlePlayer:
    def __init__(self, profile: dict, socket, table):
        self.profile = profile
        self.socket = socket
        self.table: WordleTable = table

        self.correct_answers = 0
        self.number_of_guesses = 0

        self.ready = False


class WordleTable:
    def __init__(self, room_id):
        self.room_id = room_id

        self.player_list: List[WordlePlayer] = []
        self.word_list = []
        self.current_word_index = 0

    def initialize_round(self):
        self.filter_words('storage/wordlist.txt')

    def filter_words(self, filename, word_length=5):
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

        random.shuffle(valid_words)
        self.valid_words = valid_words
        self.word_list = valid_words[:20]

    def word_list(self):
        pass

    def check_word(self, player: WordlePlayer, guessed_word: str):
        if guessed_word not in self.valid_words:
            print("Niet valsspelen, maar i kzie het nu door de vingers")
        correct_position = []
        correct_character = []
        correct_word = [letter for letter in self.word_list[self.current_word_index]]
        print(guessed_word, len(guessed_word))
        print(correct_word, len(correct_word))
        for idx, char in enumerate(guessed_word):
            if char == correct_word[idx]:
                correct_position.append(idx)
                correct_word[idx] = '_'

        for idx, char in enumerate(guessed_word):
            if char in correct_word:
                correct_character.append(idx)
                correct_word.remove(char)

        print(f"{guessed_word}, {correct_character}, {correct_position}, {correct_word}")

        return {'word': guessed_word, 'correct_position': correct_position, 'correct_character': correct_character}
