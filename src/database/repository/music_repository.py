import os
from typing import List

from discord import Member
from sqlalchemy import and_

from src import bot
from src.database.models.models import Song


def add_music(song: Song):
    session = bot.db.session()

    try:
        session.add(song)
        session.commit()
    except Exception as e:
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

    return session.query(Song).filter(Song.url == url).first()


def get_song_by_id(yt_id: str):
    session = bot.db.session()

    return session.query(Song).filter(Song.yt_id == yt_id).first()


def remove_from_owner(url: str, owner_id: int):
    session = bot.db.session()
    song = session.query(Song) \
        .filter(and_(Song.owner_id == owner_id, Song.url == url)).first()

    if song is None:
        return
    song.owner_id = -1
    session.commit()


def remove_by_file(filename: str):
    full_filename = os.path.join(bot.music_player.download_folder, filename)
    if os.path.exists(full_filename):
        os.remove(full_filename)

    session = bot.db.session()
    session.query(Song).filter(Song.file == filename).delete()
    session.commit()


def remove_unused():
    session = bot.db.session()
    songs = session.query(Song).filter(Song.owner_id == -1).all()

    for song in songs:
        # This is the only entry of the song, so remove the file.
        if len(session.query(Song)
               .filter(and_(Song.yt_id == song.yt_id, Song.owner_id != -1))
               .all()) == 0:
            print("Deleting %s" % song.file)
            remove_by_file(song.file)

    session.query(Song).filter(Song.owner_id == -1).delete()
    session.commit()


def remove_by_id(user: Member, lower, upper):
    ids = [song.id for song in get_music(user)[lower:upper]]
    session = bot.db.session()
    session.commit()

    session.query(Song).filter(Song.id.in_(ids)).delete(synchronize_session=False)
    session.commit()
    print('Done...')
