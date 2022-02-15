# noinspection PyPackageRequirements
import re
from datetime import datetime
from random import randint

import discord
import requests
from discord import Message, client
from discord.ext import commands
from discord.ext.commands import Context
from custom_emoji import CustomEmoji

from src.database.models.models import Trigger
from src.database.repository import trigger_repository, profile_repository
from src.custom_emoji import CustomEmoji


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def command_add_trigger(self, context: Context):
        message = context.message
        try:
            arr = message.content.split(" ", 2)[2].split("|", 1)

            trig = arr[0].strip()
            resp = arr[1].strip()

            trigger = Trigger(message, trig, resp)
            err = trigger_repository.add_trigger(trigger)

            if err is not None:
                await message.channel.send(err)
                return

            self.bot.update_triggers(message)
            await message.channel.send("Trigger for '%s' added." % trigger.trigger)
        except Exception as e:
            print(e)
            await message.channel.send("Trigger failed to add")

    async def command_remove_trigger(self, context: Context):
        message = context.message

        trig = message.content.split(" ", 2)[2]
        try:
            trigger_repository.remove_trigger(message.guild, trig)  # TODO check if works
            self.bot.update_triggers(message)
            await message.channel.send("Trigger '" + trig + "' removed")
        except Exception as e:
            print(e)
            await message.channel.send("Failed to remove trigger. Doesn't exist?")

    async def command_show_triggers(self, context: Context):
        message = context.message
        if len(self.bot.triggers[message.guild]) == 0:
            await message.channel.send("This server has no triggers.")
            return

        out = "```"
        out += "{0: <20}  | {1: <16}\n".format("Trigger"[:20], "Creator"[:16])
        for trigger in self.bot.triggers[message.guild]:
            if trigger is None:
                continue
            out += "{0: <20}  | {1: <16}\n".format(trigger['trigger'][:20], trigger['creator'][:16])
        out += "```"
        await message.channel.send(out)

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
        if len(message.mentions) > 0:
            url = str(message.mentions[0].avatar_url_as(size=512))
        else:
            # Get the first emoji matching the content
            url = next((emoji.url for emoji in message.guild.emojis if str(emoji) == image), None)

        if not url:
            return
        em = discord.Embed()
        em.set_image(url=url)
        await message.channel.send(embed=em)

    @commands.command()
    async def sustruck(self, context: Context):
        text = f"""▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌█▄
 {CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}{CustomEmoji.sussy}          {CustomEmoji.monkasteer} █ ▄▄
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌██████▌
▀(@)▀▀▀▀▀▀▀▀▀(@)(@)▀▀▀▀▀(@)▀"""
        await context.message.channel.send(text)

    @commands.command()
    async def roll(self, context: Context, message=None):
        """
        !roll <N>: generate a random number between 0-N (N=100 by default). Or use NdM for dnd-type rolls. (N max 1000)
        :param context:
        :param message:
        :return:
        """
        if message is None:
            value = str(randint(0, 100))
        elif "d" in message:
            d = message.split("d")
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
                upper = int(message)
            except ValueError as e:
                print(e)
                upper = 100
            value = str(randint(0, upper))
        await context.channel.send("%s rolled a %s." % (context.author.nick, value))

    @commands.command()
    async def birthday(self, context: Context, message=None):
        """
        !birthday <dd-mm-yyyy>
        """

        birthday_date = datetime.strptime(message, '%d-%m-%Y')
        user_id = context.author.id
        profile = profile_repository.get_profile(user_id=user_id)
        profile_repository.add_birthday(profile, birthday_date)

    @commands.command()
    async def kortebroek(self, context: Context):
        """
        fetch http://www.kanikeenkortebroekaan.nl
        :param context:
        :return:
        """
        url = "https://www.kanikeenkortebroekaan.nl"
        data = requests.get(url)
        m = re.search('<img src="(.*)" alt="De verwachting voor vandaag is', str(data.content))
        resp = m.group(1)

        await context.channel.send(url + resp)

    @commands.command()
    async def kill(self, context: Context):
        """
        Kills the bot, will make sure it terminates correctly.
        """
        if self.bot.music_player and self.bot.music_player.is_playing:
            self.bot.music_player.clear_and_stop(context)
        await self.bot.kill()

    @commands.command()
    async def rat(self, context: Context):
        await context.message.delete()

        await context.channel.send(f"Stay mad <@332089288839659520> {CustomEmoji.sussy}")

    @commands.command()
    async def emote(self, context: Context):
        await context.message.delete()

        emote: str = context.message.content.split()[-1]
        custom_emote = CustomEmoji().lookup_emote(emote)
        if not custom_emote:
            return await context.channel.send(f"Unable to find emote")
        await context.channel.send(f"{context.author.nick}: {custom_emote}")

    @commands.command()
    async def trigger(self, context: Context, subcommand):
        """
        Trigger words make the bot say a predefined sentence.

        Add adds a new trigger word: !trigger add <trigger> | <response>
        Show prints a list of all existing trigger words for the current server.
        Remove allows the removal of a trigger word based on trigger word. Note: This is case sensitive.
        """
        if subcommand == "add":
            await self.command_add_trigger(context)
        elif subcommand == "show":
            await self.command_show_triggers(context)
        elif subcommand == "remove":
            await self.command_remove_trigger(context)

    # @commands.command()
    # @commands.dm_only()
    # async def message(self, context: Context):
    #     if context.channel.id == context.author.dm_channel.id:
    #         channel = self.bot.get_channel(188638113982185472)
    #         await channel.send(f"{context.message.content.replace('!message ', '')}")
    #     else:
    #         pass
