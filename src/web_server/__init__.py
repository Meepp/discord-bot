print("Initialized web_server")

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
    from src.web_server import poker_socket

    # Import models and create tables
    import src.database.models.models  # noqa
    create_all_models()

    from src.web_server import poker
    app.register_blueprint(poker.bp)

print("Creating app")
create_app()


def cleanup():
    from src.web_server.poker_socket import tables
    for table in tables.values():
        table.cleanup()
