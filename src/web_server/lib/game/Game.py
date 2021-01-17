from typing import List

from web_server.lib.game.PlayerClasses import Demolisher
from web_server.lib.game.Tiles import GroundTile, Tile


def generate_board(size) -> List[List[Tile]]:
    return [[GroundTile() for i in range(size)] for j in range(size)]


class Game:
    def __init__(self, room_id):
        self.room_id = room_id

        self.players = []

        self.board = generate_board(size=30)

    def join(self, profile):
        self.players.append(Demolisher(profile, self))

    def export_board(self):
        return [[tile.to_json() for tile in row] for row in self.board]
