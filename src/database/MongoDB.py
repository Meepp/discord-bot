# import csv
# from pymongo import MongoClient
# import configparser
#
# class MongoDB:
#     def __init__(self):
#         self.config = configparser.ConfigParser()
#         self.set_config(config)
#         self.connection_string = "mongodb+srv://dtenw:0dZNkL6h8y1CGUNr@cluster0.wvrda.mongodb.net/discord-bot?retryWrites=true&w=majority"
#
#
#     def set_config(self, name):
#         self.config.read(name)
#
#     # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
#     client = MongoClient(CONNECTION_STRING)
#
#     # Create the database for our example (we will use the same database throughout the tutorial
#     db = client['discord-bot']
#
#
