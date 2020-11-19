from random import randint
from typing import List

import discord
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def explode(self, context: Context):
        """
        !explode <[emote] | [user]>: prints a larger version of the emote, or the user's profile picture.

        Explode pulls the source image for the emote or the original user profile image from the discord servers.
        This gets printed in a code block, and the original message gets removed.
        """
        message: Message = context.message
        image = message.content.split(" ")[1]

        # Show the avatar of a user.
        member = message.mentions[0]
        if member is not None:
            url = str(member.avatar_url_as(size=512))
        else:
            # Get the first emoji matching the content
            url = next((emoji.url for emoji in message.guild.emojis if str(emoji) == image), None)

        if not url:
            return
        em = discord.Embed()
        em.set_image(url=url)
        await message.channel.send(embed=em)

    @commands.command()
    async def roll(self, args, message):
        """
        !roll <N>: generate a random number between 0-N (N=100 by default). Or use NdM for dnd-type rolls. (N max 1000)
        :param args:
        :param message:
        :return:
        """
        if len(args) < 1:
            value = str(randint(0, 100))
        elif "d" in args[0]:
            d = args[0].split("d")
            n_rolls = min(int(d[0]), 1000)
            dice = int(d[1])

            rolls = [randint(1, dice) for _ in range(n_rolls)]
            s = str(sum(rolls))
            if n_rolls < 10:
                value = "%s (%s)" % (s, ", ".join(str(roll) for roll in rolls))
            else:
                value = s
        else:
            try:
                upper = int(args[0])
            except ValueError as e:
                upper = 100
            value = str(randint(0, upper))
        await message.channel.send("%s rolled a %s." % (message.author.nick, value))
