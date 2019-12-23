import discord
import queue
import os.path
import youtube_dl


class MusicPlayer:
    def __init__(self, client, download_folder):
        self.queue = queue.Queue()
        self.is_playing = False
        self.client = client
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

    def add_queue(self, guild, url, speed, downloaded=False) -> str:
        self.queue.put((guild, url, speed))

        video_title = "Unknown"
        if not downloaded:
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', None)

        if not self.is_playing:
            self.play()

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

    def done(self, error):
        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()

    def play(self):
        # If player is none and the queue is empty.
        self.is_playing = True

        # Download the youtube file and store in defined folder
        guild, url, speed = self.queue.get()
        voice = self.get_voice_by_guild(guild)
        if voice is None:
            return

        code = url.split("=")[1]
        file_location = os.path.join(self.download_folder, code)

        if not os.path.isfile(file_location):
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])

        source = discord.FFmpegPCMAudio(file_location, options='-filter:a "atempo=' + str(speed) + '"')
        voice.play(source, after=lambda e: self.done(e))
