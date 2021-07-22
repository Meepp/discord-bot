from datetime import datetime

from bson import SON
from discord import User

from src.database.models.models import Honor
from database.mongodb import get_database
import pymongo


def add_honor(honor: Honor):
    collection = get_database()['honor']

    try:
        collection.insert_one(honor.to_mongodb())
        print("Added honor")
    except Exception as e:
        print(e)


def get_honors():
    collection = get_database()['honor']
    pipeline = [
        {"$group": {"_id": "$honoree", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]
    return list(collection.aggregate(pipeline))


def get_last_honors(guild, honoring):
    collection = get_database()['honor']

    return collection.find_one({"guild_id": guild.id, "honoring": honoring}, sort=[('_id', pymongo.DESCENDING)])


def honor_allowed(guild, honoring):
    honor = get_last_honors(guild, honoring.name)

    if honor is None:
        return None

    diff = datetime.now() - honor['time']
    if diff.total_seconds() // 60 < 30:
        return 30 - diff.seconds // 60
    else:
        return None


def get_honor_count(user: User):
    collection = get_database()['honor']
    return collection.find({"honoree_id": user.id}).count()

