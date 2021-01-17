from flask import Flask
from flask_socketio import SocketIO
import logging

from src import create_all_models
from src.web_server.lib.user_session import session_user

global app
global sio


logging.basicConfig(level=logging.DEBUG)


def create_app():
    global app
    global sio
    # create and configure the app
    app = Flask(__name__)

    app.jinja_env.globals.update(session_user=session_user)

    print("Created socketio")
    sio = SocketIO(app, async_mode='gevent')
    from web_server.lib.socket import poker_socket

    # Import models and create tables
    create_all_models()

    from src.web_server import main
    app.register_blueprint(main.bp)


print("Creating app")
create_app()


def cleanup():
    from web_server.lib.socket.poker_socket import tables
    for table in tables.values():
        table.cleanup()
