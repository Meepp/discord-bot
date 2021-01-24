import threading
import time
from datetime import datetime
from enum import Enum
from typing import List, Optional

from database.models.models import Profile
from src.web_server import sio
from web_server.lib.game.PlayerClasses import Demolisher, PlayerClass, Spy, Scout, MrMole
from web_server.lib.game.Tiles import UnknownTile, Tile
from web_server.lib.game.generator import generate_board


class Phases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1


class HallwayHunters:
    def __init__(self, room_id):
        self.room_id = room_id
        self.phase = Phases.NOT_YET_STARTED
        self.player_list: List[PlayerClass] = []
        self.size = 93

        self.board, self.spawn_points = generate_board(size=self.size)

        self.initial_board_json = [[UnknownTile().to_json() for _ in range(self.size)] for _ in range(self.size)]

        self.spent_time = 0.00001
        self.ticks = 0

        self.game_loop_thread = threading.Thread(target=self.game_loop)

        self.board_changes = []

    def restart(self):
        self.board, self.spawn_points = generate_board(size=self.size)

    def game_loop(self):
        n_ticks_per_second = 60
        s_per_tick = 1 / n_ticks_per_second
        while True:
            start = datetime.now()

            self.tick()

            diff = (datetime.now() - start).total_seconds()

            self.spent_time += diff
            self.ticks += 1.
            if self.ticks % 60 == 0:
                print("Avg. Server FPS: ", 1. / (self.spent_time / self.ticks))

            # Fill time sleeping while waiting for next tick
            time.sleep(s_per_tick - diff)

    def tick(self):
        for player in self.player_list:
            # Maybe check if this is allowed, maybe not
            player.tick()

        self.update_players()
        # After having sent the update to all players, empty board changes list
        self.board_changes = []

    def add_player(self, profile, socket_id):
        for player in self.player_list:
            if player.profile.id == profile.id:
                # If the user is already in the list, overwrite the socket id to the newest one.
                player.socket = socket_id
                return

        player = Demolisher(profile, socket_id, self)
        player.change_position(self.spawn_points.pop())
        if self.phase == Phases.NOT_YET_STARTED and len(self.player_list) < 8:
            self.player_list.append(player)

        sio.emit("game_state", self.export_board(player), room=player.socket, namespace="/hallway")

    def update_players(self):
        for player in self.player_list:
            sio.emit("game_state", self.export_board(player, reduced=True), room=player.socket, namespace="/hallway")

    def export_board(self, player: PlayerClass, reduced=False):
        tiles = player.get_visible_tiles()
        data = {
                "started": self.phase == Phases.STARTED,
                "player_data": player.to_json(),
                "players": [player.to_json() for player in self.player_list],
                "visible_tiles": tiles,
            }
        if not reduced:
            data.update({
                "board": self.initial_board_json,
                "board_size": self.size
            })

        return data

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

    def set_player(self, profile, new_player):
        for i, player in enumerate(self.player_list):
            if player.profile.discord_id == profile.discord_id:
                self.player_list[i] = new_player
                return

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

    def change_tile(self, position, tile: Tile):
        self.board[position.x][position.y] = tile
        self.board_changes.append({
            "x": position.x,
            "y": position.y,
            "tile": tile.to_json()
        })
