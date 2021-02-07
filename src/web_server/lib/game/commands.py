from src.web_server.lib.game.HallwayHunters import Phases
from src.web_server.lib.game.Utils import Point
from src.web_server.lib.game.exceptions import InvalidCommand


def teleport_command(text_message, player, game):
    """
    Teleport requires x and y coordinates
    """
    split_message = text_message.split()
    if len(split_message) != 3:
        raise InvalidCommand("The teleport command requires an x and y coordinate")
    x_coordinate = int(split_message[1])
    y_coordinate = int(split_message[2])
    if 0 <= x_coordinate <= game.size or 0 <= y_coordinate <= game.size:
        player.position = Point(x_coordinate, y_coordinate)
    else:
        raise InvalidCommand("You cannot teleport outside the game")


def restart_command(game, player, room):
    if player.discord_id == room.author_id:
        game.start()
    else:
        raise InvalidCommand("Only the room owner is allowed to restart the game")


def handle_developer_command(data, game, room):
    text_message = data.get("message")[1:]
    profile = data.get("profile")
    player = game.get_player(profile)
    print(game.phase == Phases.NOT_YET_STARTED)
    if game.phase.value == Phases.NOT_YET_STARTED:
        raise InvalidCommand("The game has not even started and you are already trying to cheat!")
    if text_message.startswith('teleport'):
        teleport_command(text_message, player, game)
    if text_message.startswith('restart'):
        restart_command(game, profile, room)
