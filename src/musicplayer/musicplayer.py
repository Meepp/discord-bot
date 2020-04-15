from datetime import datetime

import discord
import queue
import os.path
import youtube_dl

from src import bot
from src.database.models.models import Song
from src.database.repository import music_repository


class MusicPlayer:
    def __init__(self, client, download_folder):
        self.queue = queue.Queue()
        self.is_playing = False
        self.client = client
        self.currently_playing = None
        self.download_folder = download_folder
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': download_folder + '/%(id)s',
            'noplaylist': True,
        }

    def add_queue(self, message, url: str, speed, downloaded=False) -> str:
        video_title = "Unknown"

        song = music_repository.get_song(url)
        if not song:
            # Creates a new entry for this song in the db.
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', None)

            song = Song(message.author, video_title, url, info_dict['id'])
            music_repository.add_music(song)

        self.queue.put((message.guild, song.url, speed))

        if not self.is_playing:
            try:
                self.play()
            except Exception as e:
                self.done(e)

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
        print("Im in", voice)
        print(voice.is_playing(), voice.is_connected())
        if voice.is_connected() and voice.is_playing():
            voice.resume()
        else:
            await message.channel.send("There is no music playing currently.")

    def done(self, error):
        if error is not None:
            print(error)

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

        # Download the youtube file and store in defined folder
        voice = bot.get_voice_by_guild(guild)
        if voice is None:
            print("Warning: attempted playing music without being in a voice channel.")
            return

        file_location = os.path.join(self.download_folder, song.yt_id)
        session = bot.db.session()

        # Download song if not yet downloaded
        if not os.path.isfile(file_location) or song.file is None:
            try:
                with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([song.url])
                song.file = song.yt_id
                session.commit()
            except Exception as e:
                print("Error: exception while downloading song:", e)
                self.done(e)
                return

        self.currently_playing = song.file or song.yt_id

        # Update latest playtime to currently.
        # TODO: Use latest playtime to remove unplayed songs from the db
        song.latest_playtime = datetime.now()

        # Add bot status change to currently playing song
        coroutine = bot.client.change_presence(activity=discord.Game(name=song.title))
        if bot.awaitables is not None:
            bot.awaitables.put_nowait(coroutine)

        source = discord.FFmpegPCMAudio(file_location, options='-filter:a "atempo=' + str(speed) + '"')

        voice.play(source, after=lambda e: self.done(e))
        session.commit()
