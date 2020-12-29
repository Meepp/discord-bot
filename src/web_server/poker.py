from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from database import db
from database.models.models import RoomModel
from database.repository import room_repository
from web_server.lib.user_session import session_profile

bp = Blueprint('poker', __name__)


print("Importing routes")


@bp.route('/')
def index():
    print("Got here.")
    rooms = room_repository.get_rooms()

    return render_template('poker/index.html', rooms=rooms)


@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        room_name = request.form['roomName']

        error = None
        if not room_name:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            session = db.session()
            room = RoomModel(room_name, session_profile())
            session.add(room)
            session.commit()

            return redirect(url_for('index'))

    return render_template('poker/create.html')


def get_room(room_id, check_author=False):
    room = room_repository.get_room(room_id)

    if check_author and room.author != session_profile():
        abort(401, "Room id {0} doesn't belong to you.".format(room_id))
    if room is None:
        abort(404, "Room id {0} doesn't exist.".format(room_id))

    return room


@bp.route('/<int:room_id>/roomSettings', methods=('GET',))
def room_settings(room_id):
    room = get_room(room_id)
    return render_template('poker/room_settings.html', room=room)


@bp.route('/<int:room_id>/game', methods=('GET',))
def game(room_id):
    room = get_room(room_id)

    return render_template('poker/game.html', room=room)

