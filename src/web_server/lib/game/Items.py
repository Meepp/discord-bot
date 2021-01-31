import random


class Item:
    def __init__(self):
        self.name = ""

    def to_json(self):
        return {
            "name": self.name
        }

    def __str__(self):
        return f"Name: {self.name}"

    __repr__ = __str__


class RubbishItem(Item):
    def __init__(self):
        super().__init__()
        chance = random.randint(0, 3)
        self.name = "rubbish_" + str(chance)
