from typing import List

from src.web_server.lib.game.Utils import Point, EntityDirections, direction_to_point
from src.web_server.lib.game.exceptions import InvalidAction
from src.web_server.lib.game.entities.movable_entity import MovableEntity
from src.web_server.lib.game.entities.Spell import SpellEntity
from src.web_server.lib.game.entities.Passive import Passive


class EnemyClass(MovableEntity):
    def __init__(self, sprite_name: str, game, unique_identifier: str):
        super().__init__(unique_identifier, game)
        self.MAX_MOVEMENT = 10
        self.sprite_name = sprite_name
        self.spawn_position = Point(1, 1)
        self.position = Point(1, 1)
        self.last_position = self.position
        self.class_name = None

        self.dead = False
        self.can_move = True

        self.updated = True

        self.movement_cooldown = 10  # Ticks
        self.movement_timer = 0
        self.movement_queue = []
        self.moving = False

        self.direction = EntityDirections.DOWN

        from src.web_server.lib.game.HallwayHunters import HallwayHunters
        self.game: HallwayHunters = game

        self.passives: List[Passive] = []

        # Fixed stats
        self.damage = 2
        self.hp = 1

    def collide(self, other):
        print(self.hp, other.card.damage_type, other.card.damage)
        if isinstance(other, SpellEntity):
            other: SpellEntity
            if other.card.damage_type != "heal":
                self.hp -= other.card.damage
            if self.hp <= 0:
                self.die()

    def start(self):
        super().start()
        self.direction = EntityDirections.DOWN

    def die(self):
        self.dead = True
        self.can_move = False

    def tick(self):
        super().tick()

        for passive in self.passives[:]:
            passive.tick()
            if passive.time == 0:
                self.passives.remove(passive)

    def to_json(self):
        state = super().to_json()
        state.update({
            "dead": self.dead,
            "sprite_name": self.sprite_name,
        })
        return state

    def post_movement_action(self):
        pass

    def prepare_movement(self):
        # TODO: Pathfinding to nearest player
        self.movement_queue = [
            Point(-1, 0),
            Point(-1, 0),
            Point(-1, 0),
            Point(0, -1),
            Point(0, -1),
            Point(0, -1),
            Point(1, 0),
            Point(1, 0),
            Point(1, 0),
            Point(0, 1),
            Point(0, 1),
            Point(0, 1),
        ]
