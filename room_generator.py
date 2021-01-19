import random
from typing import List

from src.web_server.lib.game.Tiles import WallTile, Tile, GroundTile


def maze_generator(matrix, x, y):
    matrix[x][y] = GroundTile()
    carved_cells = [(x, y)]
    while carved_cells != []:
        pass


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


def generate_board(size) -> List[List[Tile]]:
    base = [[WallTile() for i in range(size)] for j in range(size)]

    room_generator(base, size)

    base[0] = [WallTile() for i in range(size)]
    print(*base, sep="\n")
    return base


generate_board(32)
