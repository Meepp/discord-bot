from pymongo import MongoClient
import configparser
import os


class MongoDB:
    def __init__(self, config):
        self.config = configparser.ConfigParser()
        self.set_config(config)
        self.connection_string = f"mongodb+srv://{self.config['DEFAULT']['username']}:" \
                                 f"{self.config['DEFAULT']['password']}@" \
                                 f"cluster0.wvrda.mongodb.net/{self.config['DEFAULT']['database']}?" \
                                 f"retryWrites=true&w=majority"

        self.client = MongoClient(self.connection_string, connect=False)
        self.db = self.client["discord-bot"]

    def set_config(self, name):
        self.config.read(name)


mongodb = MongoDB(f"{os.path.dirname(os.path.realpath(__file__))}\dbconfig.conf").db
