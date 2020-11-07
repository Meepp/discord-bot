import io
import queue
import threading
import time
from datetime import datetime

import discord
import youtube_dl

from src import bot
from src.database.models.models import Song
from src.database.repository import music_repository

FFMPEG_OPTS = {"options": "-vn -loglevel quiet -hide_banner -nostats", "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}


class MusicPlayer:
    def __init__(self, client, download_folder):
        self.queue = queue.Queue()
        self.is_playing = False
        self.client = client
        self.currently_playing = None  # Url of the song
        self.download_folder = download_folder

    def skip_queue(self, num):
        temp = queue.Queue()
        for i in range(self.queue.qsize()):
            if i == num:
                continue
            temp.put(self.queue.queue[i])

        self.queue = temp

    def add_queue(self, message, url: str, speed) -> str:
        video_title = "Unknown"

        song = music_repository.get_song(url)
        if not song:
            song = Song(message.author, "", url)
            music_repository.add_music(song)
            # print("Song not in db, downloading remote.")
            # bot.downloader.get(url, message.author)

        self.queue.put((message.guild, url, speed))

        if not self.is_playing:
            try:
                self.play()
            except Exception as e:
                message.channel.send("Error:" + str(e))
        return video_title

    def clear(self, message):
        self.queue = queue.Queue()
        self.is_playing = False
        voice = bot.get_voice_by_guild(message.guild)
        voice.stop()

    def skip(self, guild):
        voice = bot.get_voice_by_guild(guild)
        voice.stop()

    async def pause(self, message):
        voice = bot.get_voice_by_guild(message.guild)

        if voice.is_connected() and voice.is_playing():
            voice.pause()
        else:
            await message.channel.send("There is no music playing currently.")

    async def unpause(self, message):
        voice = bot.get_voice_by_guild(message.guild)
        if voice.is_connected() and voice.is_playing():
            voice.resume()
        else:
            await message.channel.send("There is no music playing currently.")

    def done(self, error):
        if error is not None:
            print("Exception while playing file:", error)

        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()
        else:
            print("Setting status to nothing active")
            coroutine = bot.client.change_presence(activity=None)
            if bot.awaitables is not None:
                bot.awaitables.put_nowait(coroutine)

    def play(self):
        # Blocking Queue get, waits for an item to enter the queue.
        guild, url, speed = self.queue.get()

        self.is_playing = True
        song = music_repository.get_song(url)

        # Check if the bot is in a voice channel currently.
        voice = bot.get_voice_by_guild(guild)
        if voice is None:
            print("Warning: attempted playing music without being in a voice channel.")
            return

        session = bot.db.session()

        # Extract the source location url from the youtube url.
        ydl = youtube_dl.YoutubeDL()
        try:
            r = ydl.extract_info(url, download=False)
        except Exception as e:
            # Retry after half a second
            time.sleep(0.25)
            r = ydl.extract_info(url, download=False)

        song.title = r["title"]
        formats = r["formats"]

        # TODO: Attempt to fetch audio only stream, if this errors fallback on formats[0]
        # source_url = None
        # for f in formats:
        #     # audio only format defined by youtube
        #     if f["format_id"] == "251":
        #         source_url = f["url"]
        #         break

        source_url = formats[0]["url"]

        if not source_url:
            # TODO: Error handling
            return

        audio_source = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTS)
        self.currently_playing = song.url

        # Update latest playtime to currently.
        song.latest_playtime = datetime.now()

        # Add bot status change to currently playing song
        coroutine = bot.client.change_presence(activity=discord.Game(name=song.title))
        if bot.awaitables is not None:
            bot.awaitables.put_nowait(coroutine)

        voice.play(audio_source, after=lambda e: self.done(e))
        session.commit()
