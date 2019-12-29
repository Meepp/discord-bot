import configparser
import discord
from src.database.database import Database  # noqa


class Bot:
    commands = {}

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.client = discord.Client()
        self.db = Database("database.db")
        self.triggers = dict()
        self.music_player = None

    def update_triggers(self, message):
        self.triggers[message.guild] = trigger_repository.get_triggers(message.guild)

    def set_config(self, name):
        self.config.read(name)

    def start(self):
        self.music_player = MusicPlayer(self.client, self.config["DEFAULT"]["AudioDownloadFolder"])
        self.client.run(self.config["DEFAULT"]["DiscordAPIKey"])

    def kill(self):
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
