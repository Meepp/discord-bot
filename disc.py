import discord
from discord.ext.commands import Bot
from discord.ext import commands

Client = discord.Client()
bot_prefix = "!bot "
client = commands.Bot(command_prefix=bot_prefix)

@client.event
async def on_ready():
print("Bot Online!")

@client.command(pass_context=True)
async def ree():
await client.say("<:REE:394490500960354304> <:REE:394490500960354304> <:REE:394490500960354304> <:REE:394490500960354304>")

@client.command(pass_context=True)
async def pubg():
await client.say("<:REE:394490500960354304> <:REE:394490500960354304> <:REE:394490500960354304> <:REE:394490500960354304>")


client.run("MzQwMTk3NjgxMzExNzc2NzY4.DSQ39A.sGYDQgt8-5lbOK7N0L5EDQRAatk")
