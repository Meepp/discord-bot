from collections import namedtuple

from database.models.models import Profile
from web_server.lib.game.Tiles import GroundTile, WallTile
from web_server.lib.game.Utils import Point, PlayerAngles
from web_server.lib.game.exceptions import InvalidAction


class PlayerClass:
    def __init__(self, profile: Profile, socket_id, game):
        self.name = ""
        self.profile = profile
        self.ability_cooldown = 0
        self.position = Point(1, 1)
        self.pre_move = Point(1, 1)
        self.cooldown_timer = 0
        self.ready = False
        self.old_positions = set()
        self.direction = PlayerAngles.DOWN

        from web_server.lib.game.HallwayHunters import HallwayHunters
        self.game: HallwayHunters = game

        self.socket = socket_id

    def ability(self):
        pass

    def tick(self):
        self.cooldown_timer = max(0, self.cooldown_timer - 1)

        self.position = self.pre_move
        self.old_positions.add(self.position)

        self.ready = False

    def suggest_move(self, move: Point):
        if move.x == self.position.x + 1:
            self.direction = PlayerAngles.RIGHT
        elif move.x == self.position.x - 1:
            self.direction = PlayerAngles.LEFT
        elif move.y == self.position.y + 1:
            self.direction = PlayerAngles.DOWN
        elif move.y == self.position.y - 1:
            self.direction = PlayerAngles.UP

        if self.position == move:
            raise InvalidAction("You are already on this tile.")

        if move.x > self.game.size or move.y > self.game.size or move.x < 0 or move.y < 0:
            raise InvalidAction("You cannot move out of bounds.")

        if not self.game.board[move.x][move.y].movement_allowed:
            raise InvalidAction("You cannot move on this tile.")

        if abs(self.position.x - move.x) + abs(self.position.y - move.y) != 1:
            raise InvalidAction("You cannot move more than one square per turn.")

        self.pre_move = move
        self.set_ready()

    def set_ready(self):
        self.ready = True
        self.game.tick()

    def to_json(self, owner=True):
        # Default dictionary to see other players name
        state = {
            "username": self.profile.discord_username,
            "ready": self.ready,
            "position": self.position.to_json(),
            "name": self.name,
            "direction": self.direction.value,
        }
        # In case you are owner add player sensitive information to state
        if owner:
            state.update({
                "pre_move": self.pre_move.to_json(),
                "cooldown": self.ability_cooldown,
                "cooldown_timer": self.cooldown_timer,
            })
        return state


class Demolisher(PlayerClass):
    def __init__(self, profile, socket_id, game):
        super().__init__(profile, socket_id, game)

        self.name = "Demolisher"
        self.ability_cooldown = 30

    def ability(self):
        position = self.position
        # if self.cooldown_timer != 0:
        #     raise InvalidAction("Ability on cooldown, %d remaining." % self.cooldown_timer)
        old_position = Point(position.x, position.y)

        if self.direction == PlayerAngles.UP:
            if isinstance(self.game.board[position.x][position.y - 1], WallTile):
                print("Before", position)
                position.y = position.y - 1
                print("After", position)
        elif self.direction == PlayerAngles.DOWN:
            if isinstance(self.game.board[position.x][position.y + 1], WallTile):
                position.y = position.y + 1
        elif self.direction == PlayerAngles.LEFT:
            if isinstance(self.game.board[position.x - 1][position.y], WallTile):
                position.x = position.x - 1
        elif self.direction == PlayerAngles.UP:
            if isinstance(self.game.board[position.x + 1][position.y], WallTile):
                position.x = position.x + 1
        print(position, old_position)
        if old_position == position:
            raise InvalidAction("You cannot demolish this tile right now")
        print("To demolish wall", position)
        self.game.board[position.x][position.y] = GroundTile()
        self.cooldown_timer = self.ability_cooldown

    def change_position(self, point):
        self.position = point
        self.old_positions.add(point)
