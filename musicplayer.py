import discord
import queue
import os.path
import youtube_dl


ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp/%(id)s',
    'noplaylist' : True,
}

class MusicPlayer:
    def __init__(self, client):
        self.queue = queue.Queue()
        self.is_playing = False
        self.client = client

    def get_voice_by_guild(self, guild):
        for voice in self.client.voice_clients: # TODO: Dont put a voice object in the queue
            if voice.guild == guild:
                return voice

    def add_queue(self, guild, url, speed) -> str:
        self.queue.put((guild, url, speed))

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
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

        # Download the youtube file and store in temp
        # TODO: Remove file when done.
        guild, url, speed = self.queue.get()
        voice = self.get_voice_by_guild(guild)
        if voice is None:
            return
            
        code = url.split("=")[1]

        if not os.path.isfile("temp/"+code):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        source = discord.FFmpegPCMAudio("temp/"+code, options='-filter:a "atempo=' + str(speed) + '"')
        voice.play(source, after=lambda e: self.done(e))