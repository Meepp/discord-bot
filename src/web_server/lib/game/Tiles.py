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
        return " "

    def __eq__(self, other):
        return other == " "

    __repr__ = __str__


class WallTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "edge_l"

        self.movement_allowed = False
        self.opaque = True

    def __repr__(self):
        return "W"


class TopLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tl"


class TopRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tr"


class BottomLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_bl"


class BottomRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_br"


class TopWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "edge_t"


class LeftWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "edge_l"


class RightWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "edge_r"


class BottomWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "edge_b"
