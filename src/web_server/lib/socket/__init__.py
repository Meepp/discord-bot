from flask import request
from flask_socketio import join_room

from database.repository import room_repository
from web_server import sio
from web_server.lib.socket.game_socket import join_game
from web_server.lib.socket.poker_socket import join_poker, leave_poker


@sio.on('join')
def on_join(data):
    room_id = int(data['room'])
    join_room(room=room_id)

    room = room_repository.get_room(room_id)
    if room.type == "poker":
        join_poker(room_id)
    elif room.type == "game":
        join_game(room_id)



@sio.event
def disconnect():
    leave_poker(request.sid)