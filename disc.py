import discord
from discord.ext.commands import Bot
from discord.ext import commands
from random import randint
import queue
import time
import youtube_dl
import os.path

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

    async def pause(self, channel):
        if self.player and not self.player.is_done():
            self.player.pause()
        else:
            await client.send_message(channel, "There is no music playing currently.")

    async def unpause(self, channel):
        if self.player and not self.player.is_done():
            self.player.resume()
        else:
            await client.send_message(channel, "There is no music playing currently.")

    def done(self, error):
        print(error)
        if self.player and not self.player.is_done():
            self.player.stop()

        self.is_playing = False

        # Continue playing from the queue
        if not self.queue.empty():
            self.play()

    def play(self):
        # If player is none and the queue is empty.
        self.is_playing = True

        # Download the youtube file and store in temp
        # TODO: Remove file when done.
        voice, url = self.queue.get();
        code = url.split("=")[1];

        if not os.path.isfile("temp/"+code):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        self.player = voice.create_ffmpeg_player("temp/"+code, after=lambda e: self.done(e))
        self.player.volume = 0.2
        self.player.start()

musicplayer = MusicPlayer()

async def add_queue(url):
    musicplayer.queue.put(url)

    if musicplayer.is_playing:
        return

    musicplayer.play()

async def command_pause(channel):
    await musicplayer.pause(channel)

async def command_unpause(channel):
    await musicplayer.unpause(channel)

# Adds a song to the queue
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
    # musicplayer.done(None)
    musicplayer.player.stop()

async def command_kill(message):
    if musicplayer.is_playing:
        musicplayer.player.stop()
    await client.logout()

async def command_help(channel):
    help_text = "```Available commands:\n \
    !ree      : Let the bot REEEEEEEEEEEEEEEEEEEEEEEEEEE\
    !pubg     : Roept de pubmannen op voor een heerlijk maaltijd kippendinner! \
    !roll     : Rol een dobbelsteen, !roll 5 rolt tussen de 0 en de 5\
    !join     : De bot joint je voice channel\
    !fuckoff  : De bot verlaat je voice channel\
    !music    : De bot voegt een youtube filmpje aan de queue (geef een link als argument mee) \
    !pause    : Pauzeert het huidige youtube filmpje\
    !unpause  : Resumes het huidige youtube filmpje\
    !joinpub  : Met deze commando join je de Pubmannen groep\
    !leavepub : Met deze commando verlaat je de Pubmannen groep\
    !skip     : Skipt het huidige youtube filmpje \"
    await client.send_message(channel, help_text)

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

    elif cmd == "!pause":
        await command_pause(message.channel)

    elif cmd == "!unpause":
        await command_unpause(message.channel)

    elif cmd == "!joinpub":
        await command_joinpub(message)

    elif cmd == "!leavepub":
        await command_leavepub(message)

    elif cmd == "!skip":
        await command_skip(message)

    elif cmd == "!kill":
        await command_kill(message)
    elif cmd == "!help":
        await command_help(message.channel)


with open('key', 'r') as f:
    client.run(f.readline().strip())
