import configparser
import threading
import asyncio

import discord
from src.database.database import Database  # noqa
from src.musicplayer.youtube_search import YoutubeAPI


class Bot:
    commands = {}

    def __init__(self):
        self._running = True
        self.config = configparser.ConfigParser()
        self.client = discord.Client()
        self.db = Database("database.db")
        self.triggers = dict()
        self.music_player: MusicPlayer = None
        self.youtube_api: YoutubeAPI = None
        self.awaitables = None

    async def _awaitable_handler(self):
        self.awaitables = asyncio.Queue()
        print("Starting awaitable handler thread.")
        while self._running:
            awaitable = await self.awaitables.get()

            await asyncio.ensure_future(awaitable)

    def start_handlers(self):
        asyncio.ensure_future(self._awaitable_handler())

    def update_triggers(self, message):
        self.triggers[message.guild] = trigger_repository.get_triggers(message.guild)

    def set_config(self, name):
        self.config.read(name)

    def start(self):
        self.music_player = MusicPlayer(self.client, self.config["DEFAULT"]["AudioDownloadFolder"])
        self.youtube_api = YoutubeAPI(self.config["DEFAULT"]["YoutubeAPIKey"])
        self.client.run(self.config["DEFAULT"]["DiscordAPIKey"])

    def kill(self):
        self._running = False
        self.client.logout()

    @classmethod
    def register_command(cls, *args):
        def decorator(fn):
            cls.commands[args[0]] = fn

        return decorator


bot = Bot()

from src.commands.commands import *  # noqa
from src.event_handlers.messages import *  # noqa
from src.musicplayer.musicplayer import MusicPlayer  # noqa
