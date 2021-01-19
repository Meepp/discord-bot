import random
from typing import List

from src.web_server.lib.game.Tiles import WallTile, Tile, GroundTile


def room_generator(board: List[List[Tile]], size, attempts=50):
    def room_fits(_x, _y, _width, _height):
        """
        Check if a room fits if all the squares around it and itself are walls
        """
        for i in range(_x - 1, _x + _width + 1):
            for j in range(_y - 1, _y + _height + 1):
                if not isinstance(board[i][j], WallTile):
                    return False
        return True

    def carve_room(_x, _y, _width, _height):
        """
        Replace tiles with ground tiles for all in the x, y, width, height range.
        """
        for i in range(_x, _x + _width):
            for j in range(_y, _y + _height):
                board[i][j] = GroundTile()
        return True

    min_size = 3
    max_size = 7
    for _ in range(attempts):
        width = random.randint(min_size, max_size)
        height = random.randint(min_size, max_size)

        x = random.randint(1, size - width - 1)
        y = random.randint(1, size - height - 1)
        if room_fits(x, y, width, height):
            carve_room(x, y, width, height)
from web_server.lib.game.Utils import Point


def maze_generator(matrix, start_point):
    def check_point(_point, _orig_point):
        # If the left point is not the original point, and it is already ground, it is not valid
        lp = Point(_point.x - 1, _point.y)
        if lp != _orig_point and isinstance(matrix[_point.x - 1][_point.y], GroundTile):
            return False
        rp = Point(_point.x + 1, _point.y)
        if rp != _orig_point and isinstance(matrix[_point.x + 1][_point.y], GroundTile):
            return False
        bp = Point(_point.x, _point.y - 1)
        if bp != _orig_point and isinstance(matrix[_point.x][_point.y - 1], GroundTile):
            return False
        tp = Point(_point.x, _point.y + 1)
        if tp != _orig_point and isinstance(matrix[_point.x][_point.y + 1], GroundTile):
            return False
        return True

    matrix[start_point.x][start_point.y] = GroundTile()
    carved_cells = [start_point]
    while carved_cells != []:
        current_cell = carved_cells[-1]
        potential_cells = []
        x = current_cell.x
        y = current_cell.y
        if x - 1 != 0 and isinstance(matrix[x - 1][y], WallTile):
            point = Point(x - 1, y)
            if check_point(point, current_cell):
                potential_cells.append(point)
        if x + 2 != len(matrix) and isinstance(matrix[x + 1][y], WallTile):
            point = Point(x + 1, y)
            if check_point(point, current_cell):
                potential_cells.append(point)
        if y - 1 != 0 and isinstance(matrix[x][y - 1], WallTile):
            point = Point(x, y - 1)
            if check_point(point, current_cell):
                potential_cells.append(point)
        if y + 2 != len(matrix[x]) and isinstance(matrix[x][y + 1], WallTile):
            point = Point(x, y + 1)
            if check_point(point, current_cell):
                potential_cells.append(point)

        if len(potential_cells) != 0:
            next_cell = potential_cells[random.randint(0, len(potential_cells) - 1)]
            matrix[next_cell.x][next_cell.y] = GroundTile()
            carved_cells.append(next_cell)
        else:
            carved_cells.remove(current_cell)
    return matrix



def generate_board(size) -> List[List[Tile]]:
    base = [[WallTile() for i in range(size)] for j in range(size)]

    room_generator(base, size)

    maze_generator(base, Point(1, 1))
    maze_generator(base, Point(1, size - 2))
    maze_generator(base, Point(size - 2, 1))
    maze_generator(base, Point(size - 2, size - 2))

    print(*base, sep="\n")
    return base


generate_board(32)
