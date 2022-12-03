from typing import Optional

from src.web_server.lib.game.Items import Item
from src.web_server.lib.game.Utils import Point


class Tile:
    """
    Generic class, don't initialize this directly, use subclasses instead.
    """

    def __init__(self):
        self.image = "center"
        self.movement_allowed = True
        self.opaque = True
        self.animation_ticks = 0
        self.finish_animation = False
        self.item: Optional[Item] = None

    def to_json(self):
        return {
            "image": self.image,
            "movement_allowed": self.movement_allowed,
            "opaque": self.opaque,
            "animation_ticks": self.animation_ticks,
            "finish_animation": self.finish_animation,
            "item": self.item.to_json() if self.item else None,
        }

    def __str__(self):
        return f"Image: {self.image}, mov_allowed: {self.movement_allowed}, opaque: {self.opaque}, item: {self.item}"

    __repr__ = __str__


class GroundTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "floor"

        self.movement_allowed = True
        self.opaque = False

    def __str__(self):
        return " "

    def __eq__(self, other):
        return other == " "

    __repr__ = __str__


class UnknownTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "void"

        self.movement_allowed = False
        self.opaque = True

    def __str__(self):
        return " "

    def __eq__(self, other):
        return other == " "

    __repr__ = __str__


class WallTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "void"

        self.movement_allowed = False
        self.opaque = True

    def __repr__(self):
        return "W"


class DoorTile(Tile):
    def __init__(self):
        super().__init__()
        self.image = "door"

        self.movement_allowed = True
        self.opaque = True

    def __repr__(self):
        return "D"


class TopLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tl"


class TopLeftCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tl_top"


class TopRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tr"


class TopRightCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_tr_top"


class BottomLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_bl"


class ChestTile(Tile):
    def __init__(self, player):
        super().__init__()
        self.image = "chest"
        self.player = player
        self.movement_allowed = False
        self.opaque = False


class BottomLeftCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_bl_top"


class BottomRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_br"


class BottomRightCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "corner_br_top"


class InnerTopLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_tl"


class InnerTopLeftCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_tl_top"


class InnerTopRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_tr"


class InnerTopRightCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_tr_top"


class InnerBottomLeftCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_bl"


class InnerBottomLeftCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_bl_top"


class InnerBottomRightCornerWall(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_br"


class InnerBottomRightCornerWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "inner_corner_br_top"


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


class BottomWall2(WallTile):
    def __init__(self):
        super().__init__()
        self.image = "edge_b_top"


class LadderTile(Tile):
    def __init__(self, position: Point):
        super().__init__()
        self.image = "ladder"
        self.opaque = False
        self.movement_allowed = True
        self.other_ladder = None
        self.position = position


class CameraTile(Tile):
    def __init__(self, position: Point):
        super().__init__()
        self.image = "camera"
        self.opaque = False
        self.movement_allowed = True
        self.position = position
        self.top_left_position = Point(position.x - 2, position.y - 2)
        self.bottom_right_position = Point(position.x + 3, position.y + 3)