import asyncio
import queue
import threading

import youtube_dl

from src import bot
from src.database.models.models import Song
from src.database.repository import music_repository


class Downloader:
    def __init__(self, folder):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': folder + '/%(id)s',
            'noplaylist': True,
        }
        self.lock = threading.Condition()
        self.download_queue = queue.Queue()

        self.thread = threading.Thread(target=self._poll_download)
        self.thread.start()

    def _poll_download(self):
        print("Starting asynchronous downloader thread.", flush=True)
        while bot.is_running():
            url = self.download_queue.get()
            print("Async download of url %s" % url, flush=True)

            self.lock.acquire()
            song = music_repository.get_song(url)

            try:
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([url])

                session = bot.db.session()
                song.file = song.yt_id
                session.commit()
            except Exception as e:
                print("Error: exception while downloading song:", e, flush=True)

            self.lock.notify()
            self.lock.release()

    def get(self, url, author):
        # Creates a new entry for this song in the db.
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', None)

        song = Song(author, video_title, url, info_dict['id'])
        music_repository.add_music(song)

        self.download_queue.put_nowait(url)
