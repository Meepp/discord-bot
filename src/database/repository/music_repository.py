import os
from typing import List

from discord import Member
from sqlalchemy import and_

from database import db
from src.database.models.models import Song


def add_music(song: Song):
    session = db.session()

    try:
        session.add(song)
        session.commit()
    except Exception as e:
        session.rollback()


def get_music(owner: Member = None) -> List[Song]:
    session = db.session()

    sub = session.query(Song)
    if not owner:
        return sub.all()
    else:
        return sub.filter(Song.owner_id == owner.id).all()


def get_song(url: str):
    session = db.session()

    return session.query(Song).filter(Song.url == url).first()


def remove_from_owner(url: str, owner_id: int):
    session = db.session()
    song = session.query(Song) \
        .filter(and_(Song.owner_id == owner_id, Song.url == url)).first()

    if song is None:
        return
    song.discord_id = -1
    session.commit()


def remove_unused():
    session = db.session()
    songs = session.query(Song).filter(Song.owner_id == -1).all()

    for song in songs:
        # This is the only entry of the song, so remove the file.
        if len(session.query(Song)
               .filter(and_(Song.file == song.file, Song.owner_id != -1))
               .all()) == 0:
            print("Deleting %s" % song.file)

    session.query(Song).filter(Song.owner_id == -1).delete()
    session.commit()


def remove_by_id(user: Member, lower, upper):
    ids = [song.id for song in get_music(user)[lower:upper]]
    session = db.session()
    session.commit()

    session.query(Song).filter(Song.id.in_(ids)).delete(synchronize_session=False)
    session.commit()
    print('Done...')


def show_playlist(mention, page=0, page_size=15):
    songs = get_music(mention)

    n_pages = int(len(songs) / page_size) + 1
    page = (page + n_pages) % n_pages

    out = "```\n%ss playlist (%d / %d):\n" % (mention.nick, page, n_pages)
    for i in range(page * page_size, min(len(songs), (page + 1) * page_size)):
        song = songs[i]
        out += "%d: %s | %s\n" % (i, song.title, song.owner)
    out += "```"
    return out


def query_song_title(query):
    session = db.session()
    return session.query(Song).filter(Song.title.like("%" + query + "%")).all()