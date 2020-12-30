from gevent import monkey
monkey.patch_all()

from geventwebsocket import WebSocketServer

host = '0.0.0.0'
port = 5000


if __name__ == "__main__":
    from src.web_server import app
    from src import bot

    app.secret_key = bot.config["WEBSERVER"]["SECRET"]

    http_server = WebSocketServer((host, port), app, debug=True)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        app.cleanup()
        http_server.stop()
