import os
import queue
import re
from random import randint, shuffle

import discord
from discord import Message, Guild
from discord.ext import commands
from discord.ext.commands import Context

from src import bot
from src.custom_emoji import CustomEmoji
from src.database.models.models import Trigger, Report, Honor
from src.database.repository import trigger_repository, report_repository, music_repository, honor_repository
from src.database.repository.music_repository import remove_from_owner



@bot.register_command("fuckoff")
async def command_fuckoff(args, message):
    """
    !fuckoff: makes the bot leave its currently active voice channel.

    :param args:
    :param message:
    :return:
    """
    for x in bot.client.voice_clients:
        if x.guild == message.guild:
            bot.music_player.clear(message)
            return await x.disconnect()


@bot.register_command("queue")
async def command_queue(args, message):
    """
    !queue: show the queue of the first few upcoming songs.
    :param args:
    :param message:
    :return:
    """
    size = bot.music_player.queue.qsize()

    page = 0
    if len(args) > 0:
        try:
            page = int(args[0])
        except ValueError as e:
            pass

    page_size = bot.settings.page_size

    out = "```\nComing up page (%d / %d):\n" % (page, bot.music_player.queue.qsize() / page_size)
    for i in range(page * page_size, min(size, (page + 1) * page_size)):
        _, url, _ = bot.music_player.queue.queue[i]
        song = music_repository.get_song(url)
        out += "%d: %s | %s\n" % (i, song.title, song.owner)
    out += "```"
    await message.channel.send(out, delete_after=30)


@bot.register_command("playlist")
async def command_playlist(args, message: Message):
    """
    !playlist (@user | delete @user <id>)

    !playlist @user: shows the playlist of the given user in order of addition (oldest first).
    !playlist delete @user <id>: deletes a song from a players playlist.
       Id can be a range (e.g. 0:10) which will delete all numbers in the range [0, 10)
    """
    if len(message.mentions) == 0:
        await message.channel.send("Mention a player to change or see their playlist.")
        return

    if args[0] == "delete":
        if message.author != message.mentions[0]:
            await message.channel.send("Cannot delete songs from another user's playlist.")
            return

        try:
            if ":" in args[2]:
                data = args[2].split(":", 1)
                low, upp = int(data[0]), int(data[1])
            else:
                low = int(args[2])
                upp = low + 1
        except ValueError as e:
            await message.channel.send("Invalid number or range, should be either a single number or a range in the form 'n:m'.")
            return

        music_repository.remove_by_id(message.mentions[0], lower=low, upper=upp)

        await message.channel.send("Successfully deleted %d songs from the playlist." % (upp - low))
    else:
        mention = message.mentions[0]
        page = 0
        for arg in args:
            try:
                page = int(arg)
                break
            except ValueError:
                pass

        out = music_repository.show_playlist(mention, page)
        await message.delete()
        message = await message.channel.send(out)
        music_repository.playlists[message.id] = (mention, page)
        await message.add_reaction(CustomEmoji.jimbo)
        await message.add_reaction(CustomEmoji.arrow_left)
        await message.add_reaction(CustomEmoji.arrow_right)


@bot.register_command("delete")
async def command_delete(args, message):
    """
    !delete: deletes the currently playing song from your playlist.

    :param args:
    :type message: Message
    """

    if len(args) > 0:
        try:
            num = int(args[0])
        except ValueError as e:
            num = 0
        _, url, _ = bot.music_player.queue.queue[num]
        remove_from_owner(url, message.author.id)
        bot.music_player.skip_queue(num)
    else:
        remove_from_owner(bot.music_player.currently_playing, message.author.id)
        bot.music_player.skip(message.guild)


@bot.register_command("skip")
async def command_skip(args, message):
    """
    !skip: skips the currently playing song, and starts playing the next (if available)

    :param args:
    :param message:
    :return:
    """
    bot.music_player.skip(message.guild)


@bot.register_command("clear")
async def command_clear(args, message):
    """
    !clear: Clears the queue of all songs, does not kill the currently playing song.

    :param args:
    :param message:
    :return:
    """
    if bot.music_player:
        bot.music_player.queue = queue.Queue()


@bot.register_command("kill")
async def command_kill(args, message):
    """
    !kill: kills the bot, will make sure it terminates correctly.

    :param args:
    :param message:
    :return:
    """
    if bot.music_player and bot.music_player.is_playing:
        bot.music_player.clear(message)
    await bot.kill()


@bot.register_command("trigger")
async def command_trigger(args, message):
    """
    !trigger <add | show | remove>: Trigger words make the bot say a predefined sentence.

    Add adds a new trigger word: !trigger add <trigger> | <response>
    Show prints a list of all existing trigger words for the current server.
    Remove allows the removal of a trigger word based on trigger word. Note: This is case sensitive.
    :param args:
    :param message:
    """
    if args[0] == "add":
        await command_add_trigger(message)
    elif args[0] == "show":
        await command_show_triggers(message)
    elif args[0] == "remove":
        await command_remove_trigger(message)
    else:
        pass  # TODO: Give user feedback


async def command_add_trigger(message):
    try:
        arr = message.content.split(" ", 2)[2].split("|", 1)

        trig = arr[0].strip()
        resp = arr[1].strip()

        trigger = Trigger(message)
        trigger.trigger = trig
        trigger.response = resp
        err = trigger_repository.add_trigger(trigger)

        if err is not None:
            await message.channel.send(err)
            return

        bot.update_triggers(message)
        await message.channel.send("Trigger added")
    except Exception as e:
        print(e)
        await message.channel.send("Trigger failed to add")


async def command_remove_trigger(message):
    trig = message.content.split(" ", 2)[2]
    # TODO: Only created users or mods can delete

    try:
        trigger_repository.remove_trigger(message.guild, trig)
        bot.update_triggers(message)
        await message.channel.send("Trigger '" + trig + "' removed")
    except Exception as e:
        print(e)
        await message.channel.send("Failed to remove trigger. Doesn't exist?")


async def command_show_triggers(message):
    if len(bot.triggers[message.guild]) == 0:
        await message.channel.send("This channel has no triggers.")
        return

    out = "```"
    out += "{0: <20}  | {1: <16}\n".format("Trigger"[:20], "Creator"[:16])
    for trigger in bot.triggers[message.guild]:
        if trigger is None:
            continue
        out += "{0: <20}  | {1: <16}\n".format(trigger.trigger[:20], trigger.author[:16])
    out += "```"
    await message.channel.send(out)
