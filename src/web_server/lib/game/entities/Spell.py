from src.web_server.lib.game.Utils import direction_to_point
from src.web_server.lib.game.cards.Card import Card
from src.web_server.lib.game.entities.movable_entity import MovableEntity


class SpellEntity(MovableEntity):
    def __init__(self, player, card: Card, unique_identifier: str, game):
        super().__init__(unique_identifier, game)
        self.position = player.position
        self.direction = player.direction
        self.movement_cooldown = 4
        self.card = card
        self.movement_queue = [direction_to_point(player.direction)] * card.ability_range

    def movement_action(self):
        move = super().movement_action()
        # TODO: Check enemy damage

    def post_movement_action(self):
        super().post_movement_action()
        self.alive = False

    def to_json(self):
        state = super().to_json()
        state.update({
            "sprite_name": self.card.name
        })
        return state
