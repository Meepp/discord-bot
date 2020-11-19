import asyncio
import io
import queue
import string
import threading

import discord
import requests
import youtube_dl

from src import bot, randint
from src.database.models.models import Song
from src.database.repository import music_repository

ALLOWED_CHARS = string.digits + string.ascii_letters


def generate_code():
    """
    Generates a random string of 32 chars long. Can be used for file names.
    :return:
    """
    length = 32
    return "".join(ALLOWED_CHARS[randint(0, len(ALLOWED_CHARS) - 1)] for _ in range(length))


class Downloader:
    def __init__(self, folder):
        self.folder = folder

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
        }
        self.event: threading.Event = threading.Event()
        self.lock: threading.Lock = threading.Lock()
        self.download_queue = queue.Queue()

        self.is_running = True

        self.thread = threading.Thread(target=self._poll_download)
        self.thread.start()

    def download_file(self, url, buffer, file):
        """
        This downloads a file in chunks and writes to the given filepointer.

        :param buffer: the buffer to use to download the file into.
        :param url: url from where to download.
        :param file: file location for final download storage.
        :return:
        """
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                buffer.write(chunk)

        # After download is done, write buffer to disk.
        with open(file, "w+") as f:
            f.write(buffer)

    def _poll_download(self):
        print("Starting asynchronous downloader thread.")
        while self.is_running:
            try:
                url, file = self.download_queue.get(timeout=1)

                print("Async download of url %s" % url, flush=True)

                self.event.clear()
                self.lock.acquire()
                song = music_repository.get_song(url)
                session = db.session()

                # Extract the source location url from the youtube url.
                ydl = youtube_dl.YoutubeDL()
                r = ydl.extract_info(url, download=False)
                source_url = r['url']

                buffer = io.BytesIO()
                thr = threading.Thread(target=self.download_file, args=(source_url, buffer, file))
                audio_source = discord.PCMAudio(buffer)

                session.commit()

                self.lock.release()
                self.event.set()
            except queue.Empty as e:
                pass
        print("Gracefully terminated downloader thread.")

    def get(self, url, author):
        # Creates a new entry for this song in the db.
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', None)

        print("Got here with title: %s" % video_title)

        random_code = generate_code()

        song = Song(author, video_title, url)
        song.file = random_code
        music_repository.add_music(song)

        self.download_queue.put_nowait((url, random_code))

    def kill(self):
        self.is_running = False
        self.thread.join()
