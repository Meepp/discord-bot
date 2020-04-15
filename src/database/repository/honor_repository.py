from datetime import datetime

from sqlalchemy import func

from src import bot
from src.database.models.models import Honor


def add_honor(honor: Honor):
    session = bot.db.session()

    try:
        session.add(honor)
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()


def get_honors(guild):
    session = bot.db.session()

    sub = session.query(Honor, func.count(Honor.honoree_id)) \
        .filter(Honor.guild_id == guild.id) \
        .group_by(Honor.honoree_id) \
        .order_by(func.count(Honor.honoree_id).desc()) \
        .all()

    return sub


def get_last_honors(guild, honoring):
    session = bot.db.session()

    return session.query(Honor) \
        .filter(Honor.guild_id == guild.id) \
        .filter(Honor.honoring == honoring) \
        .order_by(Honor.time.desc()) \
        .first()


def honor_allowed(guild, honoring):
    honor = get_last_honors(guild, honoring.name)

    if honor is None:
        return None

    diff = datetime.now() - honor.time
    if diff.seconds // 60 < 30:
        return 30 - diff.seconds // 60
    else:
        return None
