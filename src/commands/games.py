# from discord import User, Message, Reaction
# from discord.ext import commands
# from discord.ext.commands import Context
#
# from custom_emoji import CustomEmoji
# from database import mongodb as db
# from database.models.models import RoomModel
# from database.repository import room_repository, profile_repository
#
#
# async def poker_message_check(reaction: Reaction, user: User):
#     room = room_repository.find_room_by_message_id(reaction.message.id)
#
#     if room is None:
#         return False
#
#     url = "http://84.107.225.27:5000/%d/game?id=%d" % (room.id, user.id)
#
#     await user.send("Follow the link below to join %s's %s game; \"%s\"\n%s" % (room.author, room.type, room.name, url))
#
#     return True
#
#
# class Games(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#
#     @commands.command()
#     async def poker(self, context: Context, title: str):
#         profile = profile_repository.get_profile(user=context.author)
#
#         # Create new room
#         room = RoomModel(title, profile, "poker")
#
#         message = await context.channel.send('''```%s's Poker room\n%s\nClick Jimbo to join.```''' % (context.author.name, title))
#         room.message_id = message.id
#         message: Message
#
#         session = db.session()
#         session.add(room)
#         session.commit()
#
#         await message.add_reaction(CustomEmoji.jimbo)
#
#     @commands.command()
#     async def hallway(self, context: Context, title: str):
#         profile = profile_repository.get_profile(user=context.author)
#
#         # Create new room
#         room = RoomModel(title, profile, "hallway")
#
#         message = await context.channel.send(
#             '''```%s's Hallway Hunters room\n%s\nClick Jimbo to join.```''' % (context.author.name, title))
#         room.message_id = message.id
#         message: Message
#
#         session = db.session()
#         session.add(room)
#         session.commit()
#
#         await message.add_reaction(CustomEmoji.jimbo)
