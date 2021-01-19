from typing import Optional

from web_server.lib.game.Items import Item


class Tile:
    """
    Generic class, don't initialize this directly, use subclasses instead.
    """

    def __init__(self):
        self.image = "center"
        self.movement_allowed = True
        self.opaque = True
        self.item: Optional[Item] = None

    def to_json(self):
        return {
            "image": self.image,
            "movement_allowed": self.movement_allowed,
            "opaque": self.opaque,
            "item": self.item.to_json() if self.item else None,
        }

    def __str__(self):
        return f"Image: {self.image}, mov_allowed: {self.movement_allowed}, opaque: {self.opaque}, item: {self.item}"

    __repr__ = __str__


class GroundTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "center"

        self.movement_allowed = True
        self.opaque = False

    def __str__(self):
        return "G"

    def __eq__(self, other):
        return other == "G"

    __repr__ = __str__

class UnmarkedTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "center"

        self.movement_allowed = True
        self.opaque = False

    def __str__(self):
        return "U"

    def __eq__(self, other):
        return other == "U"

    __repr__ = __str__


class WallTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "edge_l"

        self.movement_allowed = False
        self.opaque = True

    def __str__(self):
        return "W"

    def __eq__(self, other):
        return other == "W"

    __repr__ = __str__
