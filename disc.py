import os.path
import re
import discord
from discord.ext.commands import Bot
from discord.ext import commands
from random import randint
from musicplayer import MusicPlayer
import time
from PIL import Image
import requests
from io import BytesIO
import json
from pprint import pprint
import requests
from database import DataBase

with open('key', 'r') as f:
    keys = f.readlines()
keys = [x.strip() for x in keys]

client = discord.Client()
musicplayer = MusicPlayer(client)

async def command_roll(message, args):
    if len(args) < 1:
        nmax = 100
    else:
        try:
            nmax = (int)(args[0])
        except:
            nmax = 100

    await message.channel.send(message.author.nick + " rolled a " + (str)(randint(0, nmax)))

async def command_join(message, args):
    if message.author.voice.channel is not None:
        try:
            await message.author.voice.channel.connect()
        except Exception as e:
            print("Hallo", e)
            await message.channel.send("I have already joined a voice channel nibba.")

async def command_fuckoff(message):
    for x in client.voice_clients:
        if x.guild == message.guild:
            musicplayer.clear(message)
            return await x.disconnect()

async def add_queue(guild, url, message):    
    try:
        speed = float(message.content.split(' ')[-1])
    except:
        speed = 1.0

    title = musicplayer.add_queue(guild, url, speed)
    
    await message.channel.send("Queueing: " + title)
    await message.delete()

async def command_pause(channel):
    await musicplayer.pause(channel)

async def command_unpause(channel):
    await musicplayer.unpause(channel)

# Adds a song to the queue
async def command_music(message, args):
    if len(args) < 1:
        return

    await add_queue(message.guild, args[0], message)

async def command_joinpub(message):
    for role in message.guild.roles:
        if role.name == "@Pubmannen":
            await message.author.add_roles(role)

async def command_leavepub(message):
    for role in message.guild.roles:
        if role.name == "@Pubmannen":
            await message.author.add_roles(role)

async def command_skip(message):
    musicplayer.skip(message.guild)

async def command_kill(message):
    if musicplayer and musicplayer.is_playing:
        musicplayer.clear(message)
    await client.logout()

async def command_explode(image, message):
    # hacky
    if "@" in image:
        for member in message.guild.members:
            if member.mention.replace("!", "") == image.replace("!", ""):
                em = discord.Embed()
                em.set_image(url=member.avatar_url)
                await message.channel.send(embed=em)
    else:
        for emoji in message.guild.emojis:
            if str(emoji) == image:
                em = discord.Embed()
                em.set_image(url=emoji.url)
                await message.channel.send((message.author.nick or message.author.name)+":", embed=em)
                await message.delete()

async def command_stats(player, channel):
    data = pubgapi.player(player)
    print(data)


async def command_kerstpuzzel(number, message):
    filename = os.path.join("kerstpuzzel", number + ".png")
    await message.channel.send("Kerstpuzzel " + number, file=discord.File(filename))


async def command_add_trigger(message):
    global triggers
    arr = message.content.split(" ", 2)[2].split("|", 1)
    name = message.author.name

    trig = arr[0].strip()
    resp = arr[1].strip()

    if len(trig) < 3 or len(trig) > 50:
        await message.channel.send("Trigger length must be   50 > n > 3 ")
        return 

    try:
        db.execute("INSERT INTO triggers VALUES ('" + trig + "', '" + resp + "', '" + name + "')")
        triggers = [trigger for trigger in db.select_all()]
        await message.channel.send("Trigger added")
    except Exception as e:
        print(e)
        await message.channel.send("Trigger failed to add")


async def command_remove_trigger(message):
    global triggers
    trig = message.content.split(" ", 2)[2]
    name = message.author.name  # TODO: Only users can self-delete

    if len(trig) < 3 or len(trig) > 50:
        await message.channel.send("Trigger length must be   50 > n > 3 ")
        return 

    try:
        db.delete_trigger(trig)
        triggers = [trigger for trigger in db.select_all()]
        await message.channel.send("Trigger '" + trig + "' removed")
    except:
        await message.channel.send("Failed to remove trigger. Doesn't exist?")


async def command_show_triggers(message):
    global triggers

    triggers = [trigger for trigger in db.select_all()]

    out = "```"
    out += "{0: <50} | {1: <32} | {2: <16}\n".format("Trigger"[:50], "Response"[:32], "Creator"[:16])
    for trig, resp, user in triggers:
        out += "{0: <50} | {1: <32} | {2: <16}\n".format(trig[:50], resp[:32], user[:16])
    out += "```"
    await message.channel.send(out)




async def command_help(channel):
    help_text = "```Available commands:\n\
  !ree     : Let the bot REEEEEEEEEEEEEEEEEEEEEEEEEEE\n\
  !pubg    : Roept de pubmannen op voor een heerlijk maaltijd kippendinner!\n\
  !roll    : Rol een dobbelsteen, !roll 5 rolt tussen de 0 en de 5\n\
  !join    : De bot joint je voice channel\n\
  !fuckoff : De bot verlaat je voice channel\n\
  !music   : De bot voegt een youtube filmpje aan de queue (geef een link als argument mee)\n\
  !pause   : Pauzeert het huidige youtube filmpje\n\
  !unpause : Resumes het huidige youtube filmpje\n\
  !joinpub : Met deze commando join je de Pubmannen groep\n\
  !trigger <add|remove|show>: Add or remove trigger words.\n\
  !leavepub: Met deze commando verlaat je de Pubmannen groep\n\
  !skip    : Skipt het huidige youtube filmpje ```"
    await channel.send(help_text)

@client.event
async def on_message(message):
    msg_array = message.content.split()

    if len(msg_array) == 0:
        return

    cmd = msg_array[0]
    args = msg_array[1:]

    if message.mention_everyone or cmd == "!ree":
        await message.channel.send("<:REE:394490500960354304> <:REE:394490500960354304> \
<:REE:394490500960354304> <:REE:394490500960354304>")
    elif cmd == "!pubg":
        await message.channel.send("<@&385799510879895552> time for <:dinner:392014108498722826>")

    elif cmd == "!roll":
        await command_roll(message, args)

    elif cmd == "!join":
        await command_join(message, args)

    elif cmd == "!fuckoff":
        await command_fuckoff(message)

    elif cmd == "!music":
        await command_music(message, args)

    elif cmd == "!pause":
        await command_pause(message)

    elif cmd == "!unpause":
        await command_unpause(message)

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

    elif cmd == "!explode":
        await command_explode(args[0], message)

    elif cmd == "!stats":
        await command_stats(args[0], message.channel)

    elif cmd == "!kp":
        await command_kerstpuzzel(args[0], message)
    
    elif cmd == "!trigger":
        if args[0] == "add":
            await command_add_trigger(message)
        elif args[0] == "remove":
            await command_remove_trigger(message)
        elif args[0] == "show":
            await command_show_triggers(message)

    else:
        global triggers
        if message.author.bot:
            return
        for trigger, response_message, sender in triggers:
            if trigger in message.content:
                await message.channel.send(response_message)

db = DataBase("database.db")
triggers = [trigger for trigger in db.select_all()]
print(triggers)
client.run(keys[0])
