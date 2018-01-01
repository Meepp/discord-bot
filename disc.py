import discord
from discord.ext.commands import Bot
from discord.ext import commands
from random import randint
import queue
import youtube_dl

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp/%(id)s',
    'noplaylist' : True,
}

client = discord.Client()
# bot_prefix = "!bot "
# client = commands.Bot(command_prefix=bot_prefix)

async def command_roll(message, args):
    if len(args) < 1:
        nmax = 100
    else:
        try:
            nmax = (int)(args[0])
        except:
            nmax = 100

    await client.send_message(message.channel, message.author.nick + " rolled a " + (str)(randint(0, nmax)))

async def command_join(message, args):
    if message.author.voice_channel is not None:
        try:
            await client.join_voice_channel(message.author.voice_channel)
        except:
            await client.send_message(message.channel, "I have already joined a voice channel nibba.")

async def command_fuckoff(message):
    for x in client.voice_clients:
        if x.server == message.server:
            if musicplayer.player:
                musicplayer.player.stop()
            return await x.disconnect()

class MusicPlayer:
    def __init__(self):
        self.queue = queue.Queue()
        self.is_playing = False
        self.player = None

    def done(self, error):
        print(error)
        if self.player:
            self.player.stop()
            
        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()

    def play(self):
        # If player is none and the queue is empty.
        if self.queue.empty():
            pass

        # Download the youtube file and store in temp
        # TODO: Remove file when done.
        voice, url = self.queue.get();
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        code = url.split("=")[1];

        self.is_playing = True
        self.player = voice.create_ffmpeg_player("temp/"+code, after=lambda e: self.done(e))
        self.player.volume = 0.2
        self.player.start()

musicplayer = MusicPlayer()

import time
async def add_queue(url):
    musicplayer.queue.put(url)

    if musicplayer.is_playing:
        return

    musicplayer.play()

# Adds a song to a queue
async def command_music(message, args):
    if len(args) < 1:
        return

    for voice in client.voice_clients:
        if voice.server == message.server:
            await add_queue((voice, args[0]))

async def command_joinpub(message):
    for role in message.server.roles:
        if role.name == "@Pubmannen":
            await client.add_roles(message.author, role)

async def command_leavepub(message):
    for role in message.server.roles:
        if role.name == "@Pubmannen":
            await client.remove_roles(message.author, role)

async def command_skip(message):
    musicplayer.done(None)

@client.event
async def on_message(message):
    msg_array = message.content.split()
    cmd = msg_array[0]
    args = msg_array[1:]

    if cmd == "!ree":
        await client.send_message(message.channel, "<:REE:394490500960354304> <:REE:394490500960354304> \
                          <:REE:394490500960354304> <:REE:394490500960354304>")
    elif cmd == "!pubg":
        await client.send_message(message.channel, "<@&385799510879895552> time for <:dinner:392014108498722826>")

    elif cmd == "!roll":
        await command_roll(message, args)

    elif cmd == "!join":
        await command_join(message, args)

    elif cmd == "!fuckoff":
        await command_fuckoff(message)

    elif cmd == "!music":
        await command_music(message, args)

    elif cmd == "!joinpub":
        await command_joinpub(message)

    elif cmd == "!leavepub":
        await command_leavepub(message)
    elif cmd == "!skip":
        await command_skip(message)


with open('key', 'r') as f:
    client.run(f.readline().strip())
