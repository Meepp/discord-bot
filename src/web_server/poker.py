from flask import (
    Blueprint, render_template, request
)
from werkzeug.exceptions import abort

from database.repository import room_repository, profile_repository
from src.web_server.lib.user_session import session_user, session_user_set

bp = Blueprint('poker', __name__)


def get_room(room_id, check_author=False):
    room = room_repository.get_room(room_id)

    if check_author and room.author != session_user().owner:
        abort(401, "Room id {0} doesn't belong to you.".format(room_id))
    if room is None:
        abort(404, "Room id {0} doesn't exist.".format(room_id))

    return room


@bp.route('/<int:room_id>/game', methods=('GET',))
def game(room_id):
    profile = session_user()

    if profile is None:
        user_id = request.args.get("id", None)
        if user_id is None:
            abort(400, "ID not supplied.")
        profile = profile_repository.get_profile(user_id=user_id)
        session_user_set(profile)

    room = get_room(room_id)

    return render_template('poker/game.html', room=room)

