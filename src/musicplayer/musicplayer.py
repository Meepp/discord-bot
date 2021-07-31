import asyncio
import queue
import random
from datetime import datetime
from random import shuffle

import discord
import youtube_dl
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context

from database import mongodb as db

from custom_emoji import CustomEmoji
from database.repository import profile_repository
from database.repository.music_repository import remove_from_owner
from src.database.models.models import Song, PlaylistSong
from src.database.repository import music_repository

FFMPEG_OPTS = {"options": "-vn -loglevel quiet -hide_banner -nostats",
               "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"}


async def send_music_info(channel, result):
    out = "Currently playing: %s" % result["title"]

    thumbnails = result["thumbnails"]

    em = discord.Embed()
    em.set_image(url=str(thumbnails[1]["url"]))

    await channel.send(out)


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def playlist(self, context: Context, subcommand: str, value: str = ""):
        profile = profile_repository.get_profile(context.author)

        if subcommand == "add":
            # Check if there is a playlist active for this user.
            if profile['active_playlist'] is None:
                return await context.channel.send(
                    "No playlist selected yet. Select a playlist with !playlist select <name>.")
            playlist = music_repository.get_playlist(context.author, profile['active_playlist'])

            # Add music from your current music list to this playlist
            split_message = context.message.content.split(" ")

            if value == "mymusic":
                songs = music_repository.get_music(owner=context.author)
                for s_number in split_message[3:]:
                    # You can add ranges of songs, or individual songs.
                    if ":" in s_number:
                        r = s_number.split(":")
                        numbers = range(int(r[0]), int(r[1]))
                    else:
                        numbers = [int(s_number)]

                    # Add all songs to this playlist
                    collection = db['playlistSong']
                    for number in numbers:
                        try:
                            song = songs[int(number)]
                            ps = PlaylistSong(playlist, song)
                            collection.insert(ps.to_mongodb())
                            await context.channel.send(
                                f":white_check_mark: Successfully added {song['title']} to {playlist}")
                        except IndexError:
                            await context.channel.send("Cannot add song number %d." % number)
            else:
                return await context.channel.send(
                    "Currently only adding songs which are already added in your personal playlist is supported.")
        elif subcommand == "delete":
            if profile['active_playlist'] is None:
                return await context.channel.send(
                    "No playlist selected yet. Select a playlist with !playlist select <name>.")

            # Show all songs in the active playlist for this user
            playlist = music_repository.get_playlist(context.author, profile['active_playlist'])
            songs = music_repository.get_playlist_songs(playlist)

            # Check if the delete value is valid.
            to_delete = int(value)
            if to_delete > len(songs) or to_delete < 0:
                return await context.channel.send("Select a valid playlist song id (%d < N < %d)." % (0, len(songs)))
            song = songs[to_delete]
            title = song.title

            # Delete song from db
            collection = db['playlistSong']
            collection.find_one_and_delete({"_id": song["_id"]})
            await context.channel.send(f":x: Deleted song {to_delete} - {title} from this playlist.")

        elif subcommand == "show":
            if profile['active_playlist'] is None:
                return await context.channel.send(
                    "No playlist selected yet. Select a playlist with !playlist select <name>.")

            # Show all songs in the active playlist for this user
            playlist = music_repository.get_playlist(context.author, profile['active_playlist'])
            songs = music_repository.get_playlist_songs(playlist)
            if len(songs) == 0:
                return await context.channel.send("Playlist '%s' is empty." % profile['active_playlist'])

            def formatting(i, s: dict):
                return "%d: %s" % (i, music_repository.get_song_by_id(s["song_id"])['title'])

            from utils import create_table
            # Try to convert page number
            page = 0
            try:
                page = int(value)
            except ValueError:
                pass
            table = create_table("Playlist " + profile['active_playlist'], songs, formatting, page=page)
            await context.channel.send(table)
        elif subcommand == "select":
            # Set a playlist as the active playlist for this user.
            playlist = music_repository.get_playlist(context.author, value)
            if not playlist:
                return await context.channel.send("Cannot select this playlist.")
            profile = profile_repository.update_active_playlist(profile, value)
            await context.channel.send(f"{profile['owner']} selected playlist {profile['active_playlist']}.")
        elif subcommand == "play":
            playlist = music_repository.get_playlist(context.author, profile['active_playlist'])
            if not playlist:
                return await context.channel.send("Cannot select this playlist.")

            songs = music_repository.get_playlist_songs(playlist)
            shuffle(songs)
            for song in songs:
                await self.bot.music_player.add_queue(context.message, song.url)

            await context.channel.send(
                "Added %d songs from playlist '%s' to the queue." % (len(songs), profile['active_playlist']))
        else:
            await context.channel.send("Unknown subcommand '%s'." % subcommand)

    @commands.command()
    async def mymusic(self, context: Context):
        """
        !mymusic (@user | delete @user <id>)

        !mymusic @user: shows the music of the given user in order of addition (oldest first).
        !mymusic delete @user <id>: deletes a song from a players music.
           Id can be a range (e.g. 0:10) which will delete all numbers in the range [0, 10)
        """
        message = context.message
        if len(message.mentions) == 0:
            await message.channel.send("Mention a player to change or see their playlist.")
            return

        args = message.content.split(" ")[1:]
        subcommand = args[0]
        if subcommand == "delete":
            if message.author != message.mentions[0]:
                await message.channel.send("Cannot delete songs from another user's playlist.")
                return

            try:
                if ":" in args[1]:
                    data = args[1].split(":", 1)
                    low, upp = int(data[0]), int(data[1])
                else:
                    low = int(args[2])
                    upp = low + 1
            except ValueError as e:  # TODO
                print(e)
                await message.channel.send(
                    "Invalid number or range, should be either a single number or a range in the form 'n:m'.")
                return

            deleted_song_string = music_repository.remove_by_id(message.mentions[0], lower=low, upper=upp)

            await message.channel.send(deleted_song_string)
        else:
            mention = message.mentions[0]
            page = 0
            for arg in args:
                try:
                    page = int(arg)
                    break
                except ValueError:
                    pass

            out = music_repository.show_mymusic(mention, page)
            await message.delete()
            message = await message.channel.send(out)
            self.bot.playlists[message.id] = (mention, page)
            await message.add_reaction(CustomEmoji.jimbo)
            await message.add_reaction(CustomEmoji.arrow_left)
            await message.add_reaction(CustomEmoji.arrow_right)

    @commands.command()
    async def delete(self, context: Context):
        """
        Deletes the currently playing song from your playlist.
        !delete <number> deletes the Nth entry in the queue instead.
        """
        message: Message = context.message

        args = message.content.split(" ")[1:]
        if len(args) > 0:
            try:
                num = int(args[0])
            except ValueError as e:  # TODO
                print(e)
                await context.channel.send("%s is not a valid number. (but you know this)" % args[0])
                return

            _, url = self.bot.music_player.queue.queue[num]
            deleted_song = remove_from_owner(url, message.author.id)

            self.bot.music_player.skip_queue(num)
        else:
            deleted_song = remove_from_owner(self.bot.music_player.currently_playing, message.author.id)
            await self.bot.music_player.skip(context)
        await context.channel.send(f":x: Deleted {deleted_song['title']}")


class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = queue.Queue()
        self.is_playing = False
        self.currently_playing = None  # Url of the song
        self.ydl = youtube_dl.YoutubeDL({'noplaylist': True})

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
                await self.bot.music_player.add_queue(message, song['url'])

            await message.channel.send("Queueing " + str(len(songs)) + " songs.")
            await message.delete()
        elif subcommand == "playlist":  # TODO ask functionality
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
                except ValueError as e:  # TODO
                    print(e)

            err = False
            for num in nums:
                if num >= len(songs) or num < 0:
                    if not err:
                        await message.channel.send("Playlist id should be between %d and %d" % (0, len(songs)))
                    continue

                await self.bot.music_player.add_queue(message, songs[num]['url'])

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
                    await self.bot.music_player.add_queue(message, song['url'])
                msg = "Added %d songs. (First up: %s)" % (len(songs), songs[0]['title'])
            await message.channel.send(msg)
            await message.delete()
        else:
            await self.bot.music_player.add_queue(message, subcommand)
            await message.delete()

    def skip_queue(self, num):
        temp = queue.Queue()
        for i in range(self.queue.qsize()):
            if i == num:
                continue
            temp.put(self.queue.queue[i])

        self.queue = temp

    def get_title(self, url):
        result = self.ydl.extract_info(url, download=False)
        return result["title"]

    async def add_queue(self, message, url: str):
        song = music_repository.get_song(url)

        # Check if the song is in db, if not, add it to the db
        if song is None:
            collection = db['song']

            video_title = self.get_title(url)
            song = Song(message.author, video_title, url)
            collection.insert(song.to_mongodb())

        self.queue.put((message, url))

        if not self.is_playing:
            try:
                self.play()
                print("Playing song.")
            except Exception as e:  # TODO
                print(e)
                print("Error while playing song.")

    def clear_and_stop(self, context: Context):
        self.queue = queue.Queue()
        self.is_playing = False
        context.voice_client.stop()

        # Set to not playing anything
        coro = self.bot.change_presence(activity=None)
        asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

    @commands.command()
    async def clear(self, context: Context):
        """
        !clear: Clears the queue of all songs, does not kill the currently playing song.
        """
        self.queue = queue.Queue()
        await context.message.channel.send(":eject: Queue has been cleared")

    @commands.command()
    async def skip(self, context: Context):
        if context.voice_client is not None:
            context.voice_client.stop()
            await context.message.channel.send(":next_track: Next track", )
        else:
            await context.send("Cannot skip when not connected to voice.")

    @commands.command()
    async def pause(self, context: Context):
        voice = self.bot.get_voice_by_guild(context.message.guild)

        if voice.is_connected() and voice.is_playing():
            voice.pause()
            await context.message.channel.send(":pause_button: Paused")
        else:
            await context.message.channel.send("There is no music playing currently.")

    @commands.command()
    async def unpause(self, context: Context):
        voice = self.bot.get_voice_by_guild(context.message.guild)
        if voice.is_connected() and not voice.is_playing():
            voice.resume()
            await context.message.channel.send(":arrow_forward: Resumed")
        else:
            await context.message.channel.send("There is no music playing currently.")

    @commands.command()
    async def fuckoff(self, context: Context):
        """
        Makes the bot leave its currently active voice channel.
        """
        self.clear_and_stop(context)
        await context.voice_client.disconnect()

    @commands.command()
    async def shuffle(self, context: Context):
        current_queue = list(self.bot.music_player.queue.queue)
        random.shuffle(current_queue)
        new_queue = queue.Queue()
        for entry in current_queue:
            new_queue.put(entry)
        self.bot.music_player.queue = new_queue
        await context.message.delete()

    @commands.command()
    async def queue(self, context: Context):
        """
        Show the queue of the first few upcoming songs.
        :param context:
        :return:
        """
        message = context.message
        args = message.content.split(" ")[1:]

        size = self.bot.music_player.queue.qsize()

        if size == 0:
            await message.channel.send("There are currently no songs in the queue, you should add some!",
                                       delete_after=30)
            return
        page = 0
        if len(args) > 0:
            try:
                page = int(args[0])
            except ValueError as e:  # TODO
                print(e)

        page_size = self.bot.settings.page_size

        out = "```\nComing up page (%d / %d):\n" % (page, self.bot.music_player.queue.qsize() / page_size)
        for i in range(page * page_size, min(size, (page + 1) * page_size)):
            _, url = self.bot.music_player.queue.queue[i]
            song = music_repository.get_song(url)
            out += "%d: %s | %s\n" % (i, song['title'], song['owner'])
        out += "```"
        await message.channel.send(out, delete_after=30)
        await context.message.delete()

    def done(self, error=None):
        if error is not None:
            print(error)

        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()
        else:
            coro = self.bot.change_presence(activity=None)
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
        try:
            result = self.ydl.extract_info(url, download=False)
        except Exception as e:
            # Retry after hundredth a second
            coro = asyncio.sleep(0.01)
            asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

            try:
                result = self.ydl.extract_info(url, download=False)
            except Exception as e:
                return self.done(error="Could not fetch youtube url %s" % url)

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
            song = music_repository.get_song(url)

            if song is None:
                new_song = Song(message.author, title, url)
                song = music_repository.add_music(new_song)  # TODO Check if working
            music_repository.update_latest_playtime(song)

        audio_source = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTS)
        self.currently_playing = url

        voice.play(audio_source, after=lambda error: self.done(error=error))

        coro = self.bot.change_presence(activity=discord.Game(name=title))
        asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()

        # coro = send_music_info(message.channel, result)
        # asyncio.run_coroutine_threadsafe(coro, self.bot.asyncio_loop).result()
