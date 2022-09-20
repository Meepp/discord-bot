from pymongo import DESCENDING
from discord import User, Forbidden, Message, Embed
from discord.ext import commands
from discord.ext.commands import Context

from database import mongodb as db
from database.repository import profile_repository
from custom_emoji import CustomEmoji

NAME_CHANGE_COST = 10


def format_money(money: int):
    if money > 10000000:
        return "%.02fm" % (money / 1000000.)
    if money > 100000:
        return "%.02dk" % (money / 1000)
    return "%.02f" % money


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pay(self, context: Context, user: User, amount: int):
        author_money = profile_repository.get_money(context.author)
        user_money = profile_repository.get_money(user)

        if author_money == user_money:
            return await context.channel.send(f"Are you really trying to pay yourself? {CustomEmoji.dani}")

        if amount < 1:
            return await context.channel.send(f"No stealing! {CustomEmoji.pepohmm}")

        if author_money['balance'] < amount:
            return await context.channel.send(f"You don't have enough money. {CustomEmoji.omegalul}")

        # Update balance
        profile_repository.update_money(user_money, amount)
        profile_repository.update_money(author_money, -amount)

        await context.channel.send("Transferred money successfully. New balance: %d" % author_money['balance'])

    @commands.command()
    async def balance(self, context: Context, user: User = None):
        if not user:
            profile = profile_repository.get_money(context.author)
        else:
            profile = profile_repository.get_money(user)

        await context.channel.send(f"Current balance: {format_money(profile['balance'])}")

    @commands.command()
    async def balancetop(self, context: Context):
        collection = db['profile']
        profiles = list(collection.find().sort("balance", DESCENDING).limit(15))
        body = ""
        for i, profile in enumerate(profiles):
            body += f"{i + 1}: {profile['owner']} ({format_money(profile['balance'])})\n"
        embed = Embed(title="Current top", description=body, color=0xe2e01d)

        await context.channel.send(embed=embed)

    @commands.command()
    async def namechange(self, context: Context, user: User):
        """
        Pay 10 to change somebody's nickname to whatever you want.
        """

        message: Message = context.message
        name = message.content.split(" ", 2)[2]

        profile = profile_repository.get_money(context.author)

        if profile['balance'] < NAME_CHANGE_COST:
            return await context.channel.send("Changing someones name costs %d." % NAME_CHANGE_COST)

        try:
            await context.guild.get_member(user.id).edit(nick=name)
        except Forbidden as e:
            print(e)
            return await context.channel.send("You cannot change this user's name.")

        profile_repository.update_money(profile, -NAME_CHANGE_COST)
        await context.channel.send(":white_check_mark: Successfully changed the name")