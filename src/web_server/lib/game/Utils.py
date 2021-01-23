
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_json(self):
        return {"x": self.x, "y": self.y}

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __mul__(self, other):
        if isinstance(other, int):
            return Point(self.x * other, self.y * other)
        else:
            raise NotImplemented("Only multiplying with a constant is implemented.")

    __rmul__ = __mul__

    __repr__ = __str__


class PlayerAngles:
    UP = 0
    RIGHT = 90
    DOWN = 180
    LEFT = 270

