import discord
from discord.ext.commands import Bot
from discord.ext import commands
from random import randint

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
        #try:
            await client.join_voice_channel(message.author.voice_channel)
            for voice in client.voice_clients:
                if voice.server == message.server:
                    player = await voice.create_ytdl_player('https://www.youtube.com/watch?v=5jHy0ZjkdiM')
                    player.start()
        #except:
        #    await client.send_message(message.channel, "I have already joined a voice channel nibba.")

async def command_fuckoff(message):
    for x in client.voice_clients:
        if x.server == message.server:
            return await x.disconnect()

@client.event
async def on_message(message):
    msg_array = message.content.split()
    cmd = msg_array[0]
    args = msg_array[1:]

    if cmd == '!ree':
        await client.send_message(message.channel, "<:REE:394490500960354304> <:REE:394490500960354304> \
                          <:REE:394490500960354304> <:REE:394490500960354304>")
    elif cmd == '!pubg':
        await client.send_message(message.channel, "<@&385799510879895552> time to die")

    elif cmd == "!roll":
        await command_roll(message, args)

    elif cmd == "!join":
        await command_join(message, args)

    elif cmd == "!fuckoff":
        await command_fuckoff(message)

# @client.command(pass_context=True)
# async def ree():
#     await client.say("<:REE:394490500960354304> <:REE:394490500960354304> \
#                       <:REE:394490500960354304> <:REE:394490500960354304>")
#
# @client.command(pass_context=True)
# async def pubg():
#     await client.say("<@&385799510879895552> time to die")


client.run("MzQwMTk3NjgxMzExNzc2NzY4.DSQ39A.sGYDQgt8-5lbOK7N0L5EDQRAatk")
