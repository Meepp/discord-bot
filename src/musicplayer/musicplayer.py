import asyncio
import queue
from datetime import datetime
from random import shuffle

import discord
import youtube_dl
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context

from database import db
from src.database.models.models import Song
from src.database.repository import music_repository

FFMPEG_OPTS = {"options": "-vn -loglevel quiet -hide_banner -nostats",
               "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}


async def send_music_info(channel, result):
    out = "Currently playing: %s" % result["title"]

    thumbnails = result["thumbnails"]

    em = discord.Embed()
    em.set_image(url=str(thumbnails[1]["url"]))

    await channel.send(out)


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = queue.Queue()
        self.is_playing = False
        self.currently_playing = None  # Url of the song

    @commands.command()
    async def join(self, context: Context):
        """
        !join: lets the bot join the voice channel of the person who requested.
        """
        if context.author.voice is not None:
            try:
                await context.author.voice.channel.connect()
            except discord.ClientException:
                await context.channel.send("I have already joined a voice channel.")
        else:
            await context.channel.send("You are not in a voice channel.")

    @commands.command()
    async def music(self, context: Context, subcommand):
        """
        !music (search <query> | all <user(s)> | <youtube url> | playlist <user> <playlist id(s))

        !music all <user> => play all songs in <user>'s playlist
        !music <youtube url> => download song and play
        !music playlist <user> <playlist id(s)> => pick specific songs from playlist
        """
        voice = context.voice_client
        message: Message = context.message
        if voice is None:
            await context.send("I am not in a voice channel yet, invite me with !join before playing music.")
            return

        if subcommand == "all":
            songs = []
            if len(message.mentions) == 0:
                songs = music_repository.get_music()
            else:
                for member in message.mentions:
                    songs.extend(music_repository.get_music(member))

            shuffle(songs)
            for song in songs:
                await self.bot.music_player.add_queue(message, song.url)

            await message.channel.send("Queueing " + str(len(songs)) + " songs.")
            await message.delete()
        elif subcommand == "playlist":
            if len(message.mentions) == 0:
                await message.channel.send("No players playlist selected.")
                await message.delete()
                return

            member = message.mentions[0]

            songs = music_repository.get_music(member)
            nums = []

            # Split content and ignore command and subcommand
            args = message.content.split(" ")[2:]
            for arg in args:
                try:
                    if ":" in arg:
                        data = arg.split(":", 1)
                        low, upp = int(data[0]), int(data[1])
                        nums.extend(n for n in range(max(low, 0), min(upp + 1, len(songs))))
                    else:
                        nums.append(int(arg))
                except ValueError as e:
                    pass

            err = False
            for num in nums:
                if num >= len(songs) or num < 0:
                    if not err:
                        await message.channel.send("Playlist id should be between %d and %d" % (0, len(songs)))
                    continue

                await self.bot.music_player.add_queue(message, songs[num].url, 1)

            await message.channel.send("Added %d songs" % len([num for num in nums if len(songs) > num >= 0]))
            await message.delete()
        elif subcommand == "search":
            # Split content and ignore command and subcommand
            args = message.content.split(" ")[2:]

            url = self.bot.youtube_api.search(" ".join(args))
            await self.bot.music_player.add_queue(message, url)
            await message.delete()
        elif subcommand == "like":
            # Split content and ignore command and subcommand
            args = message.content.split(" ")[2:]
            query = " ".join(args)
            songs = music_repository.query_song_title(query)
            if len(songs) == 0:
                msg = "No songs found."
            else:
                for song in songs:
                    await self.bot.music_player.add_queue(message, song.url, 1)
                msg = "Added %d songs. (First up: %s)" % (len(songs), songs[0].title)
            await message.channel.send(msg)
            await message.delete()
        else:
            url = subcommand
            await self.bot.music_player.add_queue(message, url)
            await message.delete()

    def skip_queue(self, num):
        temp = queue.Queue()
        for i in range(self.queue.qsize()):
            if i == num:
                continue
            temp.put(self.queue.queue[i])

        self.queue = temp

    async def add_queue(self, message, url: str) -> str:
        video_title = "Unknown"

        self.queue.put((message, url))

        if not self.is_playing:
            try:
                self.play()
                print("Playing song.")
            except Exception as e:
                print("Error while playing song.")
                # coro = message.channel.send("Error:" + str(e))
                # asyncio.run_coroutine_threadsafe(coro, bot.asyncio_loop).result()

        return video_title

    def clear(self, message):
        self.queue = queue.Queue()
        self.is_playing = False
        voice = self.bot.get_voice_by_guild(message.guild)
        voice.stop()

    @commands.command()
    async def skip(self, context: Context):
        if context.voice_client is not None:
            context.voice_client.stop()
        else:
            await context.send("Cannot skip when not connected to voice.")

    @commands.command()
    async def pause(self, context: Context):
        voice = self.bot.get_voice_by_guild(context.message.guild)

        if voice.is_connected() and voice.is_playing():
            voice.pause()
        else:
            await context.message.channel.send("There is no music playing currently.")

    @commands.command()
    async def unpause(self, context: Context):
        voice = self.bot.get_voice_by_guild(context.message.guild)
        if voice.is_connected() and voice.is_playing():
            voice.resume()
        else:
            await context.message.channel.send("There is no music playing currently.")

    def done(self, error):
        if error is not None:
            print(error)

        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()
        else:
            coro = self.bot.client.change_presence(activity=None)
            asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

    def play(self):
        # Blocking Queue get, waits for an item to enter the queue.
        message, url = self.queue.get()

        self.is_playing = True

        # Check if the bot is in a voice channel currently.
        voice = self.bot.get_voice_by_guild(message.guild)
        if voice is None:
            print("Warning: attempted playing music without being in a voice channel.")
            return

        # Extract the source location url from the youtube url.
        ydl = youtube_dl.YoutubeDL({'noplaylist': True})
        try:
            result = ydl.extract_info(url, download=False)
        except Exception as e:
            # Retry after tenth a second
            coro = asyncio.sleep(0.1)
            asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

            try:
                result = ydl.extract_info(url, download=False)
            except Exception as e:
                return self.done("Could not fetch youtube url %s" % url)

        # Streams have duration set to 0.
        is_stream = result["duration"] == 0
        formats = result["formats"]
        title = result["title"]

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

        # Only non streams may get added to a playlist.
        if not is_stream:
            # At this point you may add the song to the db because there are no errors.
            session = db.session()
            song = music_repository.get_song(url)

            if song is None:
                song = Song(message.author, title, url)
                music_repository.add_music(song)

            song.latest_playtime = datetime.now()
            session.commit()

        audio_source = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTS)
        self.currently_playing = url

        voice.play(audio_source, after=lambda error: self.done(error))

        coro = self.bot.change_presence(activity=discord.Game(name=title))
        asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

        # coro = send_music_info(message.channel, result)
        # asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()
