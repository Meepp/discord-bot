from discord import Guild

from database import mongodb as db
from src.database.models.models import Trigger

def get_triggers(guild: Guild):
    if guild is None:
        return None

    # TODO
    session = db.session()
    result = session.query(Trigger) \
        .filter(Trigger.guild_id == str(guild.id)) \
        .all()
    print(result)
    return result


def get_trigger(guild: Guild, name: str):
    #TODO
    session = db.session()
    return session.query(Trigger) \
        .filter(Trigger.guild_id == guild.id) \
        .filter(Trigger.trigger == name) \
        .one_or_none()


def remove_trigger(guild: Guild, name: str):
    #TODO
    session = db.session()
    trigger = get_trigger(guild, name)
    session.delete(trigger)
    session.commit()


def add_trigger(trigger: Trigger):
    #TODO
    session = db.session()

    if len(trigger.trigger) < 3 or len(trigger.trigger) > 50:
        return "Trigger length has to be 3 < n < 50"

    try:
        session.add(trigger)
        session.commit()
    except:
        session.rollback()
        return "This trigger already exists."
    return None


