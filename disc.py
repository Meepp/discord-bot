import asyncio

from src import bot


def main():
    bot.set_config("config.conf")
    bot.start()


if __name__ == "__main__":
    main()
