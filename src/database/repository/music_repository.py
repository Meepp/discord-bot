from datetime import datetime
from typing import List, Dict

from discord import Member

from src.database import mongodb as db
from src.database.models.models import Song, Playlist, PlaylistSong


def add_music(song: Song):
    collection = db['song']
    collection.insert_one(song.to_mongodb())
    return get_song(song.url)


def get_music(owner: Member = None) -> List[Dict]:
    collection = db['song']

    if not owner:
        return list(collection.find())
    else:
        return list(collection.find({"owner_id": owner.id}))


def get_song(url: str):
    collection = db['song']
    return collection.find_one({"url": url})

def get_song_by_id(_id):
    collection = db['song']
    return collection.find_one({"_id": _id})


def remove_from_owner(url: str, owner_id: int):
    collection = db['song']
    song = collection.find_one_and_delete({"owner_id": owner_id, "url": url})
    print(f"Removed {url} from {owner_id}")
    return song


def remove_unused():
    collection = db['song']
    songs = list(collection.find({"owner_id": -1}))

    for song in songs:
        # This is the only entry of the song, so remove the file.
        collection.find_one_and_delete({"_id": song['_id']})
        print("Deleting %s" % song['title'])


def remove_by_id(user: Member, lower, upper):
    songs_to_delete = get_music(user)[lower:upper]

    collection = db['song']
    out = "```\n:x: Deleted:"
    for song in songs_to_delete:
        collection.find_one_and_delete({"_id": song['_id']})
        out += f"- {song['title']} ({song['url']})\n"
    out += "```"
    return out


def show_mymusic(mention, page=0, page_size=15):
    songs = get_music(mention)

    n_pages = int(len(songs) / page_size) + 1
    page = (page + n_pages) % n_pages

    out = "```\n%ss playlist (%d / %d):\n" % (mention.nick, (page + 1), n_pages)
    for i in range(page * page_size, min(len(songs), (page + 1) * page_size)):
        song = songs[i]
        out += "%d: %s | %s\n" % (i, song['title'], song['owner'])
    out += "```"
    return out


def query_song_title(query):
    collection = db['song']
    return list(collection.find({"title": {"$regex": query, "$options": "i"}}))


def update_latest_playtime(song):
    collection = db['song']
    return collection.find_one_and_update({"url": song['url']}, {"$set": {'latest_playtime': datetime.now()}})


def get_playlist(owner, name):
    if name is None:
        return None
    collection = db['playlist']
    playlist = collection.find_one({"title": name})
    if not playlist:
        print("Creating new playlist:", name)
        playlist_id = collection.insert_one(Playlist(owner, name).to_mongodb())
        playlist = collection.find_one({"_id": playlist_id})
    return playlist


def get_playlist_songs(playlist: dict):
    collection = db['playlistSong']
    songs = list(collection.find({"playlist_id": playlist['_id']}))
    return songs
