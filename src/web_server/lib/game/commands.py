from database.repository import profile_repository
from src.web_server.lib.game.HallwayHunters import Phases
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.exceptions import InvalidCommand


def teleport_command(text_message, player, game):
    """
    Teleport requires x and y coordinates
    """
    split_message = text_message.split()
    if len(split_message) == 2:
        if split_message[-1] == "item":
            player.position = player.objective
        elif split_message[-1] == "chest":
            player.position = player.spawn_position
        else:
            other_player = profile_repository.get_profile(username=split_message[-1])
            other_player_teleport = game.get_player(other_player)
            player.position = other_player_teleport.position
    elif len(split_message) == 3:
        try:
            x_coordinate = int(split_message[1])
            y_coordinate = int(split_message[2])
        except ValueError as e:
            raise InvalidCommand("X and Y need to be integers")
        if 0 <= x_coordinate <= game.size or 0 <= y_coordinate <= game.size:
            player.position = Point(x_coordinate, y_coordinate)
        else:
            raise InvalidCommand("You cannot teleport outside the game")
    else:
        raise InvalidCommand("The teleport command requires an x and y coordinate")

def restart_command(game, player):
    if player.username == game.author:
        game.start()
    else:
        raise InvalidCommand("Only the room owner is allowed to restart the game")


def kill_command(text_message, player, game):
    split_message = text_message.split()
    if len(split_message) != 2:
        raise InvalidCommand("Command should be used as: /kill <player_name>")
    player_to_kill = game.get_player(split_message[-1])


def handle_developer_command(data, game):
    text_message = data.get("message")[1:]
    profile = data.get("profile")
    player = game.get_player(profile)
    if game.phase.value == Phases.NOT_YET_STARTED:
        raise InvalidCommand("The game has not even started and you are already trying to cheat!")
    if text_message.startswith('teleport'):
        teleport_command(text_message, player, game)
    if text_message.startswith('restart'):
        restart_command(game, profile)
    if text_message.startswith('kill'):
        kill_command(text_message, player, game)
