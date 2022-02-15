from gevent import monkey

monkey.patch_all()

from geventwebsocket import WebSocketServer

if __name__ == "__main__":
    from src.web_server import app
    from src import bot
    print("GOT HERE")
    app.secret_key = bot.config["WEBSERVER"]["SECRET"]
    host = bot.config["WEBSERVER"]["IP"]
    port = int(bot.config["WEBSERVER"]["Port"])

    http_server = WebSocketServer((host, port), app, debug=True)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        app.cleanup()
        http_server.stop()
