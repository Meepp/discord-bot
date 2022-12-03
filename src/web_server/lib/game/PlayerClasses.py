import copy
import json
import random
from typing import Optional, List

from src.web_server.lib.game.Items import Item, CollectorItem
from src.web_server.lib.game.Tiles import GroundTile, LadderTile, ChestTile
from src.web_server.lib.game.Utils import Point, PlayerAngles, direction_to_point, line_of_sight_endpoints, \
    point_interpolator
from src.web_server.lib.game.exceptions import InvalidAction
from web_server.lib.game.cards.Card import available_cards, Card

DEMOLISHER_COOLDOWN = 30  # Seconds
SPY_COOLDOWN = 30  # Seconds
SCOUT_COOLDOWN = 30  # Seconds
MRMOLE_COOLDOWN = 10  # Seconds

MOVEMENT_COOLDOWN = 8  # Ticks
SPRINT_COOLDOWN = 10 * 60  # Ticks
KILL_COOLDOWN = 10 * 60  # Ticks


class Passive(object):
    def __init__(self, time, callback, name="", args=()):
        self.name = name
        self.total_time = time
        self.time = time
        self.callback = callback
        self.args = args

    def tick(self):
        self.time -= 1
        if self.time == 0:
            self.callback(*self.args)

    def to_json(self):
        """
        Converts the passive to json, maybe for later to display all active passives

        :return:
        """
        return {
            "name": self.name,
            "time": self.time,
            "total_time": self.total_time,
        }


class PlayerState:
    READY = 0
    PROCESSING = 1
    NOT_READY = 2


class PlayerClass:
    STARTING_HAND_SIZE = 4

    def __init__(self, username: str, socket_id, game):
        # TODO: Refactor rename   name -> color
        self.MAX_MOVEMENT = 10
        self.color = ""
        self.username = username
        self.spawn_position = Point(1, 1)
        self.position = Point(1, 1)
        self.last_position = self.position
        self.class_name = None

        self.dead = False
        self.can_move = True

        self.updated = True

        self.movement_cooldown = MOVEMENT_COOLDOWN  # Ticks
        self.movement_timer = 0
        self.movement_queue = []
        self.moving = False

        self.action_state = PlayerState.NOT_READY
        self.direction = PlayerAngles.DOWN

        # The item you are holding
        self.item: Optional[Item] = None
        self.stored_items: List[Item] = []

        self.objective: Point = Point(0, 0)

        self.passives: List[Passive] = []

        self.visible_tiles = []

        from src.web_server.lib.game.HallwayHunters import HallwayHunters
        self.game: HallwayHunters = game

        self.socket = socket_id

        # Fixed stats
        self.max_hp = 15
        self.max_mana = 10
        self.mana_regen = 1

        # Active stats
        self.hp = 15
        self.mana = 5

        # Cards to play
        self.class_deck = []
        self.cards = []
        self.hand: List[Card] = []

    def start(self):
        self.stored_items = []
        self.movement_timer = 0
        self.direction = PlayerAngles.DOWN
        self.visible_tiles = self.compute_line_of_sight()
        self.generate_item()

        self.cards = copy.deepcopy(self.class_deck)
        random.shuffle(self.cards)
        print([c.name for c in self.cards])
        self.hand.extend([self.cards.pop() for _ in range(self.STARTING_HAND_SIZE)])

    def die(self):
        self.passives = []
        self.dead = True
        self.can_move = False
        self.drop_item()
        self.game.broadcast("%s died" % self.username)

    def tick(self):
        for passive in self.passives[:]:
            passive.tick()
            if passive.time == 0:
                self.passives.remove(passive)

        self.movement_timer = max(0, self.movement_timer - 1)

        last_direction = self.direction

        # Dont recompute if the player didnt move or turn
        # TODO: Update line of sight only when player is done moving (not in the middle of animation)
        if self.position != self.last_position or self.direction != last_direction:
            self.update_line_of_sight()

        self.last_position = self.position

    def update_line_of_sight(self):
        self.updated = True
        self.visible_tiles = self.compute_line_of_sight()

    def change_position(self, point):
        self.position = self.spawn_position = point

    def move(self):
        if not self.can_move:
            return

        if len(self.movement_queue) == 0:
            self.moving = False
            return

        move = self.movement_queue.pop(0)

        # Set the correct player model direction based on input
        if move.x == 1:
            self.direction = PlayerAngles.RIGHT
        elif move.x == -1:
            self.direction = PlayerAngles.LEFT
        elif move.y == 1:
            self.direction = PlayerAngles.DOWN
        elif move.y == -1:
            self.direction = PlayerAngles.UP

        # Compute temporary position based on next move
        new_position = move + self.position
        # Check move validity
        if new_position.x > self.game.size - 1 or \
                new_position.y > self.game.size - 1 or \
                new_position.x < 0 or new_position.y < 0:
            raise InvalidAction("You cannot move out of bounds.")

        tile = self.game.board[new_position.x][new_position.y]

        # TODO: Synchronize animations server side maybe
        if isinstance(tile, ChestTile) \
                and tile.player == self \
                and self.item is not None:
            self.stored_items.append(self.item)
            self.item = None
            self.generate_item()

            # Animate the chest opening and closing
            tile.animation_ticks = 20
            tile.finish_animation = True
            self.game.animations.add(tile)

        if not tile.movement_allowed:
            raise InvalidAction("You cannot move on this tile.")

        # Reset the movement timer
        self.movement_timer = self.movement_cooldown

        # Move suggestion includes the ladder logic from Mole person
        if isinstance(tile, LadderTile) and tile.other_ladder is not None:
            self.position = tile.other_ladder.position
            self.direction = PlayerAngles.UP
        else:
            self.position = self.position + move

        # Pickup item
        # TODO: Can add check of self.objective back here
        ground_item = self.game.board[self.position.x][self.position.y].item
        if ground_item is not None and self.item is None:
            if isinstance(ground_item, CollectorItem):
                self.item = ground_item
                self.game.board[self.position.x][self.position.y].item = None

        self.moving = True

    def prepare_action(self, action, extra=None):
        # We cannot do new actions while processing the queued actions
        if self.action_state == PlayerState.PROCESSING:
            return

        # We can ready or unready when we are not processing actions
        if action == "Enter":
            if self.action_state == PlayerState.READY:
                self.action_state = PlayerState.NOT_READY
            if self.action_state == PlayerState.NOT_READY:
                self.action_state = PlayerState.READY

        # We can only do actions when not ready.
        if self.action_state == PlayerState.READY:
            return
        try:
            n_action = int(action)
            self.suggest_card(n_action)
        except ValueError:
            pass

        if action == "ArrowUp":
            self.suggest_move(Point(0, -1))
        elif action == "ArrowDown":
            self.suggest_move(Point(0, 1))
        elif action == "ArrowLeft":
            self.suggest_move(Point(-1, 0))
        elif action == "ArrowRight":
            self.suggest_move(Point(1, 0))

    def suggest_move(self, move: Point):
        # Remove the last move from the stack if moving in the opposite direction
        if len(self.movement_queue) > 0 and \
                ((self.movement_queue[-1].x == -move.x and move.x != 0) or
                 (self.movement_queue[-1].y == -move.y and move.y != 0)):
            self.movement_queue.pop(-1)
            return

        if len(self.movement_queue) == self.MAX_MOVEMENT:
            return

        self.movement_queue.append(move)

    def get_interpolated_position(self):
        progress = self.movement_timer / self.movement_cooldown

        position = self.position + (-1 * direction_to_point(self.direction)) * progress
        return position

    def to_json(self):
        state = {
            "color": self.color,
            "username": self.username,
            "dead": self.dead,
            "stored_items": [item.to_json() for item in self.stored_items],
            "state": self.action_state,
            "hp": self.hp,
            "mana": self.mana,
            "max_hp": self.max_hp,
            "max_mana": self.max_mana,
            "position": self.get_interpolated_position().to_json(),
            "direction": self.direction.value,
            "moving": self.moving,
            "item": self.item.to_json() if self.item else None,
            "hand": [],
            "movement_queue": [move.to_json() for move in self.movement_queue],
            "class_name": self.class_name,
        }
        return state

    def personal_data_json(self):
        return {
            "passives": [passive.to_json() for passive in self.passives],
            "stored_items": [item.to_json() for item in self.stored_items],
            "hand": [vars(card) for card in self.hand],
        }

    def convert_class(self, new_class):
        cls = new_class(self.username, self.socket, self.game)
        cls.ready = self.action_state
        cls.color = self.color
        cls.position = self.position
        return cls

    def compute_line_of_sight(self):
        visible_positions = set()

        endpoints = line_of_sight_endpoints(self.direction)
        endpoints = [point + self.position for point in endpoints]
        for point in endpoints:
            walls = 0
            try:
                for intermediate in point_interpolator(self.position, point):
                    if not (0 <= intermediate.x < self.game.size and 0 <= intermediate.y < self.game.size):
                        break
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

    def get_visible_players(self):
        visible_tiles = self.visible_tiles
        return [player for player in self.game.player_list if player.position in visible_tiles]

    def generate_item(self):
        random_x = random.randint(0, len(self.game.board[0]) - 1)
        random_y = random.randint(0, len(self.game.board) - 1)
        while not isinstance(self.game.board[random_x][random_y], GroundTile):
            random_x = random.randint(0, len(self.game.board[0]) - 1)
            random_y = random.randint(0, len(self.game.board) - 1)

        self.objective = Point(random_x, random_y)

        self.game.board[random_x][random_y].item = CollectorItem(self.color)

    def drop_item(self):
        if self.item is not None and \
                not isinstance(self.game.board[self.position.x][self.position.y].item, CollectorItem):
            self.game.board[self.position.x][self.position.y].item = self.item
            self.item = None
            self.update_line_of_sight()

    def suggest_card(self, n_action):
        pass

    def finish_turn(self):
        self.hand.append(self.cards.pop())
        self.mana = min(self.mana + self.mana_regen, self.max_mana)


class Demolisher(PlayerClass):
    info = """Demolisher can blow up walls with its active effect."""

    def __init__(self, username: str, socket_id, game):
        super().__init__(username, socket_id, game)


class Spy(PlayerClass):
    info = "Placeholder info."

    def __init__(self, username, socket_id, game):
        super().__init__(username, socket_id, game)


class Scout(PlayerClass):
    info = """asd."""

    def __init__(self, username, socket_id, game):
        super().__init__(username, socket_id, game)

    def tick(self):
        super().tick()


class Wizard(PlayerClass):
    info = "Traditional mage class."

    def __init__(self, username, socket_id, game):
        super().__init__(username, socket_id, game)

        self.class_deck = []
        self.class_deck.extend([available_cards["fireball"]] * 10)
        self.class_deck.extend([available_cards["spear"]] * 5)
        print(self.class_deck)
