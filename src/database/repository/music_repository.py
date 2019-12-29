from typing import List

from discord import Member

from src import bot
from src.database.models.models import Song


def add_music(song: Song):
    session = bot.db.session()

    try:
        session.add(song)
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()


def get_music(owner: Member = None) -> List[Song]:
    session = bot.db.session()

    sub = session.query(Song)
    if not owner:
        return sub.all()
    else:
        return sub.filter(Song.owner_id == owner.id).all()


def get_song(url: str):
    session = bot.db.session()

    return session.query(Song).filter(Song.url == url).one_or_none()


def update_song_data(song: Song):
    session = bot.db.session()

    session.add(song)
    session.commit()