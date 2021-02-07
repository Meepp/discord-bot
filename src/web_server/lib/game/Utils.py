from enum import Enum
from math import pi

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_json(self):
        return {"x": self.x, "y": self.y}

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __eq__(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __mul__(self, other):
        if isinstance(other, int):
            return Point(self.x * other, self.y * other)
        else:
            raise NotImplemented("Only multiplying with a constant is implemented.")

    def __truediv__(self, other):
        if other == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        if isinstance(other, int):
            return Point(self.x / other, self.y / other)
        else:
            raise NotImplemented("Only multiplying with a constant is implemented.")

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise NotImplemented("Only multiplying with another Point is implemented.")

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else:
            raise NotImplemented("Only multiplying with another Point is implemented.")

    def __round__(self, n=None):
        return Point(round(self.x, n), round(self.y, n))

    __rmul__ = __mul__

    __repr__ = __str__


class PlayerAngles(Enum):
    UP = 0
    RIGHT = 90
    DOWN = 180
    LEFT = 270


def direction_to_point(direction: PlayerAngles):
    if direction == PlayerAngles.UP:
        return Point(0, -1)
    if direction == PlayerAngles.RIGHT:
        return Point(1, 0)
    if direction == PlayerAngles.DOWN:
        return Point(0, 1)
    if direction == PlayerAngles.LEFT:
        return Point(-1, 0)


LOS_CACHE = {}


def line_of_sight_endpoints(direction: PlayerAngles, distance=15):
    if LOS_CACHE == {}:
        LOS_CACHE[PlayerAngles.UP] = [Point(i - distance, -distance) for i in range(distance * 2 + 1)]
        LOS_CACHE[PlayerAngles.DOWN] = [Point(i - distance, distance) for i in range(distance * 2 + 1)]
        LOS_CACHE[PlayerAngles.LEFT] = [Point(-distance, i - distance) for i in range(distance * 2 + 1)]
        LOS_CACHE[PlayerAngles.RIGHT] = [Point(distance, i - distance) for i in range(distance * 2 + 1)]

    return LOS_CACHE[direction]


def point_interpolator(point1: Point, point2: Point, n_steps=20):
    tracker = Point(point1.x, point1.y)

    step = (point2 - point1) / n_steps

    last = None
    for i in range(20):
        current = round(tracker)
        if last != current:
            yield current
        last = current

        tracker += step

