import os

from flask import Flask
from flask_socketio import SocketIO
import logging

from src import create_all_models
from web_server.lib.user_session import session_profile

global app
global sio


logging.basicConfig(level=logging.DEBUG)


def create_app():
    global app
    global sio
    # create and configure the app
    app = Flask(__name__)

    app.jinja_env.globals.update(session_user=session_profile)

    sio = SocketIO(app, async_mode='gevent')
    from web_server import mysocket

    # Import database and setup all required
    import database.models.models

    # Import models and create tables
    import src.database.models.models  # noqa
    create_all_models()

    from web_server import poker
    app.register_blueprint(poker.bp)


create_app()


def cleanup():
    from web_server.mysocket import tables
    for table in tables.values():
        table.cleanup()
