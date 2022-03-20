from functools import wraps
from time import time

from flask import Flask
from flask_socketio import SocketIO
import logging
from engineio.payload import Payload
from src.web_server.lib.user_session import session_user

global app
global sio


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger = logging.getLogger("timing")
        logger.info(f"{f.__name__}: {te - ts}")
        return result

    return wrap


def create_logger():
    logger = logging.getLogger("timing")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("timing.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)-8s  %(message)s", datefmt="(%H:%M:%S)"))
    logger.addHandler(fh)


def create_app():
    global app
    global sio
    # create and configure the app
    app = Flask(__name__)

    app.jinja_env.globals.update(session_user=session_user)

    print("Created socketio")
    Payload.max_decode_packets = 500
    sio = SocketIO(app, async_mode='gevent')

    import src.web_server.lib.socket

    # disable all loggers from different files
    # logging.getLogger("geventwebsocket.server").setLevel(logging.ERROR)

    # Set timing logging to file for websocket functions
    create_logger()

    from src.web_server import main
    app.register_blueprint(main.bp)

    return app


def cleanup():
    from src.web_server.lib.socket.poker_socket import tables
    for table in tables.values():
        table.cleanup()
