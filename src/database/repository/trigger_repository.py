from discord import Guild

from src.database.models.models import Trigger
from src.database import mongodb as db


def get_triggers(guild: Guild):
    if guild is None:
        return None

    collection = db['trigger']
    return list(collection.find({"guild_id": guild.id}))


def get_trigger(guild: Guild, name: str):
    collection = db['trigger']

    return collection.find_one({"guild_id": guild.id, "trigger": name})


def remove_trigger(guild: Guild, name: str):
    collection = db['trigger']

    trigger = get_trigger(guild, name)
    return collection.find_one_and_delete({"_id": trigger['_id']})


def add_trigger(trigger: Trigger):
    collection = db['trigger']

    if len(trigger.trigger) < 3 or len(trigger.trigger) > 50:
        return "Trigger length has to be 3 < n < 50"

    try:
        collection.insert_one(trigger.to_mongodb())
    except:  # TODO error handle
        return "This trigger already exists."
    return None
