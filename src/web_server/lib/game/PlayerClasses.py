from collections import namedtuple

from database.models.models import Profile
from web_server.lib.game.Game import Game
from web_server.lib.game.Tiles import GroundTile
from web_server.lib.game.Utils import Point
from web_server.lib.game.exceptions import InvalidAction


class PlayerClass:
    def __init__(self, profile: Profile, game: Game):
        self.name = ""
        self.profile = profile
        self.ability_cooldown = 0
        self.position = Point(0, 0)
        self.cooldown_timer = 0
        self.game = game
        self.pre_move = Point(0, 0)

    def move(self, x, y):
        if abs(self.position.x - x) + abs(self.position.y - y) == 1:
            self.pre_move = Point(x, y)
        else:
            raise InvalidAction("You may only move one tile.")

    def ability(self, x, y):
        pass

    def tick(self):
        self.cooldown_timer = max(0, self.cooldown_timer - 1)
        self.position = self.pre_move

    def to_json(self):
        return {
            "name": self.name,
            "username": self.profile.owner,
            "position": self.position.to_json(),
            "cooldown": self.ability_cooldown,
        }


class Demolisher(PlayerClass):
    def __init__(self, profile, game):
        super().__init__(profile, game)

        self.name = "Demolisher"
        self.ability_cooldown = 30

    def ability(self, x, y):
        if self.cooldown_timer != 0:
            raise InvalidAction("Ability on cooldown, %d remaining." % self.cooldown_timer)

        if not self.game.board[x][y].movement_allowed:
            self.game.board[x][y] = GroundTile()
            self.cooldown_timer = self.ability_cooldown
