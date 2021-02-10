import math
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


def line_of_sight_endpoints(direction: PlayerAngles, distance=11):
    if LOS_CACHE == {}:
        LOS_CACHE[PlayerAngles.DOWN] = []
        LOS_CACHE[PlayerAngles.UP] = []
        LOS_CACHE[PlayerAngles.LEFT] = []
        LOS_CACHE[PlayerAngles.RIGHT] = []

        step = 25  # Amount of steps to consider when filling in the angles
        start = 1/10  # Angle in pi
        end = 9/10  # Angle in pi
        hp = math.pi / 2  # Half pi
        for i in range(1, step):
            x = ((start + i * ((end - start) / step)) * math.pi)
            LOS_CACHE[PlayerAngles.DOWN].append(Point(math.cos(x) * distance, math.sin(x) * distance))
            LOS_CACHE[PlayerAngles.LEFT].append(Point(math.cos(x + hp) * distance, math.sin(x + hp) * distance))
            LOS_CACHE[PlayerAngles.UP].append(Point(math.cos(x + 2*hp) * distance, math.sin(x + 2*hp) * distance))
            LOS_CACHE[PlayerAngles.RIGHT].append(Point(math.cos(x + 3*hp) * distance, math.sin(x + 3*hp) * distance))

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

