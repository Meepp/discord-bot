import json
from json import JSONEncoder


class DamageTypes:
    PIERCING = 0
    HEALING = 1
    FIRE = 2

    @staticmethod
    def from_txt(txt):
        lookup = {
            "prc": DamageTypes.PIERCING,
            "heal": DamageTypes.HEALING,
            "fire": DamageTypes.FIRE,
        }
        return lookup[txt]


class Card:
    def __init__(self, name, description, ability_range, radius, mana_cost, damage, damage_type: str):
        super().__init__()
        self.name = name
        self.description = description
        self.ability_range = ability_range
        self.radius = radius
        self.mana_cost = mana_cost
        self.damage = damage
        self.damage_type = damage_type


# TODO: Move this to a nice initializer
available_cards = {}

with open("src/web_server/lib/game/cards/cards.json") as f:
    cards = json.load(f)

for card_dict in cards:
    card = Card(**card_dict)
    available_cards[card.name] = card
