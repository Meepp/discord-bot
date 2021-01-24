import copy
from collections import namedtuple

from database.models.models import Profile
from web_server.lib.game.Tiles import GroundTile, WallTile, LadderTile
from web_server.lib.game.Utils import Point, PlayerAngles, direction_to_point, line_of_sight_endpoints, \
    point_interpolator
from web_server.lib.game.exceptions import InvalidAction


class PlayerClass:
    def __init__(self, profile: Profile, socket_id, game):
        self.name = ""
        self.profile = profile
        self.position = Point(1, 1)
        self.pre_move = None

        self.movement_cooldown = 5  # Ticks
        self.movement_timer = 0

        self.ability_cooldown = 0
        self.cooldown_timer = 0  # Ticks

        self.ready = False
        self.direction = PlayerAngles.DOWN

        self.visible_tiles = []

        from web_server.lib.game.HallwayHunters import HallwayHunters
        self.game: HallwayHunters = game

        self.socket = socket_id

    def ability(self):
        if self.cooldown_timer != 0:
            raise InvalidAction("Ability on cooldown, %d remaining." % self.cooldown_timer)

    def tick(self):
        self.cooldown_timer = max(0, self.cooldown_timer - 1)
        self.movement_timer = max(0, self.movement_timer - 1)
        if self.movement_timer == 0 and self.pre_move is not None:
            self.position = self.pre_move
            self.pre_move = None
            self.movement_timer = self.movement_cooldown

        self.visible_tiles = self.compute_line_of_sight()

        self.ready = False

    def change_position(self, point):
        self.position = point

    def suggest_move(self, move: Point):
        if move.x == 1:
            self.direction = PlayerAngles.RIGHT
        if move.x == -1:
            self.direction = PlayerAngles.LEFT
        if move.y == 1:
            self.direction = PlayerAngles.DOWN
        if move.y == -1:
            self.direction = PlayerAngles.UP

        new_position = move + self.position

        if new_position.x > self.game.size - 1 or new_position.y > self.game.size - 1 or new_position.x < 0 or new_position.y < 0:
            raise InvalidAction("You cannot move out of bounds.")

        tile = self.game.board[new_position.x][new_position.y]
        if not tile.movement_allowed:
            raise InvalidAction("You cannot move on this tile.")

        # Move suggestion includes the ladder logic from Mole person
        if isinstance(tile, LadderTile) and tile.other_ladder is not None:
            self.pre_move = tile.other_ladder.position
            return

        self.pre_move = new_position

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
                "cooldown": self.ability_cooldown,
                "cooldown_timer": self.cooldown_timer,
            })
        return state

    def convert_class(self, new_class):
        cls = new_class(self.profile, self.socket, self.game)
        cls.ready = self.ready
        cls.position = self.position
        return cls

    def compute_line_of_sight(self):
        visible_positions = set()

        endpoints = line_of_sight_endpoints(self.direction, distance=7)
        endpoints = [point + self.position for point in endpoints]
        for point in endpoints:
            walls = 0
            try:
                for intermediate in point_interpolator(self.position, point):
                    # Allow for one wall in line of sight
                    if walls != 0 or self.game.board[intermediate.x][intermediate.y].opaque:
                        walls += 1

                    visible_positions.add(intermediate)
                    if walls == 2:
                        break
            except IndexError:
                pass

        return list(visible_positions)

    def get_visible_tiles(self):
        return [{
            "x": position.x,
            "y": position.y,
            "tile": self.game.board[position.x][position.y].to_json()
        } for position in self.visible_tiles]


class Demolisher(PlayerClass):
    def __init__(self, profile, socket_id, game):
        super().__init__(profile, socket_id, game)

        self.name = self.__class__.__name__
        self.ability_cooldown = 30

    def ability(self):
        super().ability()
        position = copy.copy(self.position)
        old_position = Point(position.x, position.y)

        if self.direction == PlayerAngles.UP:
            if isinstance(self.game.board[position.x][position.y - 1], WallTile):
                position.y = position.y - 1
        elif self.direction == PlayerAngles.DOWN:
            if isinstance(self.game.board[position.x][position.y + 1], WallTile):
                position.y = position.y + 1
        elif self.direction == PlayerAngles.LEFT:
            if isinstance(self.game.board[position.x - 1][position.y], WallTile):
                position.x = position.x - 1
        elif self.direction == PlayerAngles.RIGHT:
            if isinstance(self.game.board[position.x + 1][position.y], WallTile):
                position.x = position.x + 1
        if old_position == position:
            raise InvalidAction("You cannot demolish this tile right now")

        self.game.board[position.x][position.y] = GroundTile()
        self.game.change_tile(position, GroundTile())
        self.cooldown_timer = self.ability_cooldown


class Spy(PlayerClass):
    def __init__(self, profile, socket_id, game):
        super().__init__(profile, socket_id, game)
        self.name = self.__class__.__name__

        self.ability_cooldown = 30

    def ability(self):
        super().ability()


class Scout(PlayerClass):
    def __init__(self, profile, socket_id, game):
        super().__init__(profile, socket_id, game)

        self.name = self.__class__.__name__
        self.ability_cooldown = 30

    def ability(self):
        super().ability()


class MrMole(PlayerClass):
    def __init__(self, profile, socket_id, game):
        super().__init__(profile, socket_id, game)

        self.name = self.__class__.__name__
        self.ability_cooldown = 30

        self.ladders = []

    def ability(self):
        super().ability()

        position = copy.copy(self.position)

        ladder = LadderTile(self.position)
        self.ladders.append(ladder)
        # You can have only two ladders, if you create more, the oldest one will get removed
        if len(self.ladders) > 2:
            to_remove_ladder = self.ladders.pop(0)
            self.game.change_tile(to_remove_ladder.position, GroundTile())
        if len(self.ladders) == 2:
            ladder.other_ladder = self.ladders[0]
            self.ladders[0].other_ladder = ladder

        self.game.change_tile(position, ladder)
