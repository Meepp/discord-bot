from pymongo import MongoClient
import configparser
import os


class MongoDB:
    def __init__(self, config):
        self.config = configparser.ConfigParser()
        self.set_config(config)
        self.connection_string = f"mongodb+srv://{self.config['MONGODB']['username']}:" \
                                 f"{self.config['MONGODB']['password']}@" \
                                 f"cluster0.wvrda.mongodb.net/{self.config['MONGODB']['database']}?" \
                                 f"retryWrites=true&w=majority"

        self.client = MongoClient(self.connection_string, connect=False)
        if self.config['MONGODB']['Development'] == "True":
            self.db = self.client["discord-bot2"]
            print("Using development database")
        else:
            self.db = self.client['discord-bot']
            print("Using production database")

    def set_config(self, name):
        self.config.read(name)


mongodb = MongoDB(f"{os.path.dirname(os.path.realpath(__file__))}\..\..\config.conf").db
