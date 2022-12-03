from datetime import datetime

import discord
from discord import User, Message, Reaction
from discord.ext import commands
from discord.ext.commands import Context
from custom_emoji import CustomEmoji
from src.database import mongodb as db
from src.database.models.models import RoomModel
from src.database.repository import room_repository, profile_repository


async def poker_message_check(reaction: Reaction, user: User):
    room = room_repository.find_room_by_message_id(reaction.message.id)

    if room is None:
        return False

    url = "http://localhost:5000/%d/game?id=%d" % (room['message_id'], user.id)

    await user.send(
        "Follow the link below to join %s's %s game; \"%s\"\n%s" % (room['author'], room['type'], room['name'], url))

    return True


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poker(self, context: Context, title: str = "Unknown"):
        await self.create_game_room(context, title, "poker")

    @commands.command()
    async def hallway(self, context: Context, title: str = "Unknown"):
        await self.create_game_room(context, title, "hallway")

    @staticmethod
    async def create_game_room(context: Context, title, game_type):
        profile = profile_repository.get_profile(user=context.author)
        if game_type == "hallway":
            game_in_message = "Hallway Hunters"
        else:
            game_in_message = "Poker"

        embed = discord.Embed(title=f"{title}",
                              description=f"{context.author.name}'s {game_in_message} room",
                              color=discord.Colour.red() if game_type == "hallway" else discord.Colour.green())
        embed.set_author(name=context.author.display_name, icon_url=context.author.avatar_url)
        embed.add_field(name="How to join", value=f"Click {CustomEmoji.jimbo} to join.")
        message = await context.channel.send(embed=embed)
        # Create new room
        room = RoomModel(title, profile, game_type, datetime.now(), message.id)
        collection = db['gameRoom']
        collection.insert_one(room.to_mongodb())
        await message.add_reaction(CustomEmoji.jimbo)
