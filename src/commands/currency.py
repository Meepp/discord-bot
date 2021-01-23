from discord import User, Forbidden, Message
from discord.ext import commands
from discord.ext.commands import Context

from database import db
from database.models.models import Profile
from database.repository import profile_repository


def format_money(money: int):
    if money > 10000000:
        return "%.1fm" % (money / 1000000.)
    if money > 100000:
        return "%.dk" % (money / 1000)
    return money


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pay(self, context: Context, user: User, amount: int):
        author_money = profile_repository.get_money(context.author)
        user_money = profile_repository.get_money(user)

        if amount < 1:
            return await context.channel.send("No stealing!")

        if author_money.balance < amount:
            return await context.channel.send("You don't have enough money.")

        # Update balance
        user_money.balance += amount
        author_money.balance -= amount

        session = db.session()
        session.commit()

        await context.channel.send("Transferred money successfully. New balance: %d" % author_money.balance)

    @commands.command()
    async def balance(self, context: Context, user: User = None):
        if not user:
            money = profile_repository.get_money(context.author)
        else:
            money = profile_repository.get_money(user)

        await context.channel.send("Current balance: %s" % format_money(money.balance))

    @commands.command()
    async def balancetop(self, context: Context):
        session = db.session()
        ids = [member.id for member in context.guild.members]
        profiles = session.query(Profile) \
            .filter(Profile.discord_id.in_(ids)) \
            .order_by(Profile.balance.desc()) \
            .limit(15) \
            .all()

        body = "\n".join("%s: %s" % (profile.discord_username, format_money(profile.balance)) for profile in profiles)
        await context.channel.send("```Current top:\n%s```" % body)

    @commands.command()
    async def namechange(self, context: Context, user: User):
        """
        Pay 10 to change somebody's nickname to whatever you want.
        """
        cost = 10

        message: Message = context.message
        name = message.content.split(" ", 2)[2]

        money = profile_repository.get_money(context.author)

        if money.balance < cost:
            return await context.channel.send("Changing someones name costs %d." % cost)

        try:
            await context.guild.get_member(user.id).edit(nick=name)
        except Forbidden as e:
            return await context.channel.send("You cannot change this user's name.")

        money.balance -= cost
        db.session().commit()
