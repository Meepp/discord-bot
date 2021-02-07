import threading
import time
from datetime import datetime
from enum import Enum
import random
from typing import List, Optional, Set

from database.models.models import Profile
from src.web_server import sio
from src.web_server.lib.game.PlayerClasses import Demolisher, PlayerClass, Spy, Scout, MrMole
from src.web_server.lib.game.Tiles import UnknownTile, Tile, ChestTile
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.generator import generate_board


print(f"Imported {__name__}")

class Phases(Enum):
    NOT_YET_STARTED = 0
    STARTED = 1


class HallwayHunters:
    def __init__(self, room_id):
        self.tick_rate = 60
        self.room_id = room_id
        self.phase = Phases.NOT_YET_STARTED
        self.player_list: List[PlayerClass] = []
        self.size = 93

        self.spawn_points: List[Point] = []
        self.board: List[List[Tile]] = []
        self.animations: Set[Tile] = set()
        # self.board, self.spawn_points = generate_board(size=self.size)

        # Generate this to send to every player initially
        self.initial_board_json = [[UnknownTile().to_json() for _ in range(self.size)] for _ in range(self.size)]

        self.spent_time = 0.00001
        self.ticks = 0
        self.finished = False

        self.game_loop_thread = threading.Thread(target=self.game_loop)
        self.game_lock = threading.Condition()

        self.board_changes = []

    def start(self):
        self.phase = Phases.STARTED
        color_set = ["blue", "red", "black", "purple", "green"]
        selected_colors = random.sample(color_set, len(self.player_list))

        self.board, self.spawn_points = generate_board(self.size, selected_colors)
        for i, player in enumerate(self.player_list):
            spawn_point = self.spawn_points[i % len(self.spawn_points)]
            player.change_position(spawn_point)
            player.name = selected_colors[i]
            player.start()
            sio.emit("game_state", self.export_board(player), room=player.socket, namespace="/hallway")

            # Connect chest to player
            chest = ChestTile(player)
            self.board[spawn_point.x][spawn_point.y + 1] = chest
            chest.image = "chest_%s" % selected_colors[i]

            sio.emit("game_state", self.export_board(player), room=player.socket, namespace="/hallway")

        self.finished = False
        self.game_lock.acquire()
        self.game_lock.notify()
        self.game_lock.release()


    def game_loop(self):
        s_per_tick = 1 / self.tick_rate
        while True:
            print("Started loop")
            while not self.finished:
                start = datetime.now()

                self.tick()

                diff = (datetime.now() - start).total_seconds()

                self.spent_time += diff
                self.ticks += 1.
                if self.ticks % self.tick_rate == 0:
                    print("Avg. Server FPS: ", 1. / (self.spent_time / self.ticks))
                    self.spent_time = 0
                    self.ticks = 0

                # Fill time sleeping while waiting for next tick
                time.sleep(s_per_tick - diff)

            self.game_lock.acquire()
            self.game_lock.wait()
            self.game_lock.release()

    def tick(self):
        for tile in list(self.animations):
            tile.animation_ticks -= 1
            # Remove tiles which are done animating
            if tile.animation_ticks == 0:
                tile.finish_animation = False
                self.animations.remove(tile)

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
        if self.phase == Phases.NOT_YET_STARTED and len(self.player_list) < 8:
            self.player_list.append(player)



    def update_players(self):
        for player in self.player_list:
            sio.emit("game_state", self.export_board(player, reduced=True), room=player.socket, namespace="/hallway")

    def export_board(self, player: PlayerClass, reduced=False):
        tiles = player.get_visible_tiles()
        data = {
            "started": self.phase == Phases.STARTED,
            "player_data": player.to_json(),
            "players": player.get_visible_players(),
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

        if len(self.player_list) == 0:
            self.finished = True
            self.phase = Phases.NOT_YET_STARTED

    def broadcast(self, message):
        sio.emit("message", message, room=self.room_id, namespace="/hallway")

    def check_readies(self):
        for player in self.player_list:
            if not player.ready:
                return False
        return True

    def in_bounds(self, position):
        return 1 < position.x < self.size - 2 and 1 < position.y < self.size - 2

    def change_tile(self, position, tile: Tile):
        if not self.in_bounds(position):
            return
        self.board[position.x][position.y] = tile
        self.board_changes.append({
            "x": position.x,
            "y": position.y,
            "tile": tile.to_json()
        })
