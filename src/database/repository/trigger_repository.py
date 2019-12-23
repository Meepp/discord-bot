from discord import Guild
from sqlalchemy.orm import Session

from src import bot
from src.database.models.models import Trigger


def get_triggers(guild: Guild):
    session = bot.db.session()
    print(str(guild.id))
    return session.query(Trigger) \
        .filter(Trigger.guild_id == str(guild.id)) \
        .all()


def get_trigger(guild: Guild, name: str):
    session = bot.db.session()
    return session.query(Trigger) \
        .filter(Trigger.guild_id == guild.id) \
        .filter(Trigger.trigger == name) \
        .one_or_none()


def remove_trigger(guild: Guild, name: str):
    session = bot.db.session()
    trigger = get_trigger(guild, name)
    session.delete(trigger)
    session.commit()


def add_trigger(trigger: Trigger):
    session = bot.db.session()

    if len(trigger.trigger) < 3 or len(trigger.trigger) > 50:
        return "Trigger length has to be 3 < n < 50"

    try:
        session.add(trigger)
        session.commit()
    except:
        session.rollback()
        return "This trigger already exists."
    return None


