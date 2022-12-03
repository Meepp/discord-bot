import os
import pathlib

import discord
from src import bot


def create_directories():
    pathlib.Path("storage").mkdir(parents=True, exist_ok=True)
    pathlib.Path("storage/data").mkdir(parents=True, exist_ok=True)
    pathlib.Path("storage/models").mkdir(parents=True, exist_ok=True)
    print("Created directories")


def main():
    create_directories()
    bot.initialize()

    # Use event handlers for emotes etc.
    import src.event_handlers.messages  # noqa
    await bot.add_cogs()
    bot.run(bot.token)


if __name__ == "__main__":
    main()
