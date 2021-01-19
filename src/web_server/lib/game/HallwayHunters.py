from enum import Enum
from typing import List, Optional

from database.models.models import Profile
from room_generator import generate_board
from src.web_server import sio
from web_server.lib.game.PlayerClasses import Demolisher, PlayerClass
from web_server.lib.game.Tiles import GroundTile, Tile, WallTile, UnknownTile
import random


class Phases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1


class HallwayHunters:
    def __init__(self, room_id):
        self.room_id = room_id
        self.phase = Phases.NOT_YET_STARTED
        self.player_list: List[PlayerClass] = []
        self.size = 30

        self.board = generate_board(size=self.size)

    def tick(self):
        if not self.check_readies():
            return
        for player in self.player_list:
            # Maybe check if this is allowed, maybe not
            player.tick()
        print("Incremented tick")

    def add_player(self, profile, socket_id):
        for player in self.player_list:
            if player.profile.id == profile.id:
                # If the user is already in the list, overwrite the socket id to the newest one.
                player.socket = socket_id
                return
        player = Demolisher(profile, socket_id, self)  # All players become demolishers by default
        if self.phase == Phases.NOT_YET_STARTED and len(self.player_list) < 8:
            self.player_list.append(player)

    def update_players(self):
        for player in self.player_list:
            sio.emit("game_state", self.export_board(player), room=player.socket, namespace="/hallway")

    def export_board(self, player: PlayerClass):
        board = [[UnknownTile() for _ in row] for row in self.board]
        for point in player.old_positions:
            for x in range(point.x - 1, point.x + 2):
                for y in range(point.y - 1, point.y + 2):
                    board[x][y] = self.board[x][y]
        return {
            "started": self.phase == Phases.STARTED,
            "player_data": player.to_json(),
            "players": [player.to_json() for player in self.player_list],
            "board": [[tile.to_json() for tile in row] for row in board],
            "board_size": self.size,
        }

    def get_player(self, profile: Profile = None, socket_id=None) -> Optional[PlayerClass]:
        combined_list = self.player_list[:]

        if profile is not None:
            for player in combined_list:
                if player.profile.discord_id == profile.discord_id:
                    return player
            return None
        elif socket_id is not None:
            for player in combined_list:
                if player.socket == socket_id:
                    return player
            return None

    def remove_player(self, profile: Profile):
        player = self.get_player(profile)

        if player in self.player_list:
            self.player_list.remove(player)

    def broadcast(self, message):
        sio.emit("message", message, room=self.room_id, namespace="/hallway")

    def check_readies(self):
        for player in self.player_list:
            if not player.ready:
                return False
        return True
