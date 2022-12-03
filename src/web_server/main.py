from flask import (
    Blueprint, render_template
)
from werkzeug.exceptions import abort

from database.repository import room_repository
from web_server.lib.game.entities.PlayerClasses import PlayerClass
from src.web_server.lib.user_session import session_user

bp = Blueprint('poker', __name__)


def get_room(room_id, check_author=False):
    room = room_repository.get_room(room_id)

    if check_author and room['author'] != session_user().discord_username:
        abort(401, "Room id {0} doesn't belong to you.".format(room_id))
    if room is None:
        abort(404, "Room id {0} doesn't exist.".format(room_id))

    return room


@bp.route('/<int:room_id>/game', methods=('GET',))
def game(room_id):
    room = get_room(room_id)
    return render_template('poker.html', room=room)


@bp.route("/hallway/<int:room_id>", methods=["GET"])
def hallway(room_id):
    room = get_room(room_id)
    return render_template('hallway.html', room=room, classes=PlayerClass.__subclasses__())


@bp.route('/wordle/<int:room_id>', methods=('GET',))
def wordle(room_id):
    return render_template('wordle.html', room=room_id)


@bp.route('/capture/<int:room_id>', methods=('GET',))
def capture(room_id):
    return render_template('capture.html', room=room_id)
