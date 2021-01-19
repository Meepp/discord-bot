import random
from typing import List

from src.web_server.lib.game.Tiles import WallTile, Tile, GroundTile
from web_server.lib.game.Utils import Point


def maze_generator(matrix, start_point):
    matrix[start_point.x][start_point.y] = GroundTile()
    carved_cells = [start_point]
    while carved_cells != []:
        current_cell = carved_cells[-1]
        potential_cells = []
        x = current_cell.x
        y = current_cell.y
        print(x, y)
        if x - 1 != 0 and isinstance(matrix[x - 1][y], WallTile):
            potential_cells.append(Point(x - 1, y))
        if x + 2 != len(matrix) and isinstance(matrix[x + 1][y], WallTile):
            potential_cells.append(Point(x + 1, y))
        if y - 1 != 0 and isinstance(matrix[x][y - 1], WallTile):
            potential_cells.append(Point(x, y - 1))
        if y + 2 != len(matrix[x]) and isinstance(matrix[x][y + 1], WallTile):
            potential_cells.append(Point(x, y + 1))

        if len(potential_cells) != 0:
            next_cell = potential_cells[random.randint(0, len(potential_cells) - 1)]
            matrix[next_cell.x][next_cell.y] = GroundTile()
            carved_cells.append(next_cell)
        else:
            carved_cells.remove(current_cell)
    return matrix


#
# def room_generator(board: List[List[Tile]], size, attempts=20):
#     def room_fits(_x, _y, _width, _height):
#         for i in range(_x, _width):
#             for j in range(_y, _height):
#                 if not isinstance(board[_x][_y], WallTile):
#                     return False
#         return True
#
#     def carve_room(_x, _y, _width, _height):
#         for i in range(_x, _width):
#             for j in range(_y, _height):
#                 board[_x][_y] = GroundTile()
#         return True
#
#     min_size = 3
#     max_size = 7
#     for _ in range(attempts):
#         width = random.randint(min_size, max_size)
#         height = random.randint(min_size, max_size)
#
#         x = random.randint(0, size - width)
#         y = random.randint(0, size - height)
#
#         if room_fits(x, y, width, height):
#             carve_room(x, y, width, height)


def generate_board(size) -> List[List[Tile]]:
    base = [[WallTile() for i in range(size)] for j in range(size)]

    maze_generator(base, Point(1, 1))

    print(*base, sep="\n")
    return base


generate_board(5)
