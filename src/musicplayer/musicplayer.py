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
        self.deletables = []
        self.download_folder = download_folder
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': download_folder + '/%(id)s',
            'noplaylist': True,
        }

    def get_voice_by_guild(self, guild):
        for voice in self.client.voice_clients:
            if voice.guild == guild:
                return voice

    async def add_queue(self, message, url, speed, downloaded=False) -> str:
        video_title = "Unknown"
        if not downloaded:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', None)

        # Creates a new entry for this song in the db.
        song = music_repository.get_song(url)
        if not song:
            song = Song(message.author, video_title, url, info_dict['id'])
            music_repository.add_music(song)

        self.queue.put((message.guild, song, speed))

        if not self.is_playing:
            await self.play()

        return video_title

    def clear(self, message):
        self.queue = queue.Queue()
        self.is_playing = False
        voice = self.get_voice_by_guild(message.guild)
        voice.stop()

    def skip(self, guild):
        voice = self.get_voice_by_guild(guild)
        voice.stop()

    async def pause(self, message):
        voice = self.get_voice_by_guild(message.guild)

        if voice.is_connected() and voice.is_playing():
            voice.pause()
        else:
            await message.channel.send("There is no music playing currently.")

    async def unpause(self, message):
        voice = self.get_voice_by_guild(message.guild)

        if voice.is_connected() and not voice.is_playing():
            voice.resume()
        else:
            await message.channel.send("There is no music playing currently.")

    async def done(self, error):
        print(error)
        self.is_playing = False

        for deletable in self.deletables:
            os.remove(deletable)

        self.deletables = []

        # Continue playing from the queue
        if not self.queue.empty():
            await self.play()

    async def play(self):
        # If player is none and the queue is empty.
        self.is_playing = True

        # Download the youtube file and store in defined folder
        guild, song, speed = self.queue.get()
        voice = self.get_voice_by_guild(guild)
        if voice is None:
            return

        file_location = os.path.join(self.download_folder, song.yt_id)
        self.currently_playing = song.title

        # Download song if not yet downloaded
        if not os.path.isfile(file_location) or song.file is None:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([song.url])
            song.file = song.yt_id

        # Update latest playtime to currently.
        # This can be used to later remove all unplayed songs from the db
        song.latest_playtime = datetime.now()
        music_repository.update_song_data(song)

        # TODO: Investigate if program can be refactored to not have the music player update discord status
        await bot.client.change_presence(activity=discord.Game(name=song.title))
        source = discord.FFmpegPCMAudio(file_location, options='-filter:a "atempo=' + str(speed) + '"')
        voice.play(source, after=lambda e: self.done(e))

