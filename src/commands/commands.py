import os
import queue
import re
from random import randint, shuffle

import discord
from discord import Message, Guild

from src import bot
from src.database.models.models import Trigger, Report, Honor
from src.database.repository import trigger_repository, report_repository, music_repository, honor_repository
from src.database.repository.music_repository import remove_from_owner


def is_valid_youtube_url(input):
    return re.match(r"(http(s)?://)?(www\.)?(youtube\.com|youtu\.be)/.*$", input)


@bot.register_command("roll")
async def command_roll(args, message):
    if len(args) < 1:
        nmax = 100
    else:
        try:
            nmax = (int)(args[0])
        except:
            nmax = 100

    await message.channel.send(message.author.nick + " rolled a " + str(randint(0, nmax)))


@bot.register_command("join")
async def command_join(args, message):
    if message.author.voice.channel is not None:
        try:
            await message.author.voice.channel.connect()
        except Exception as e:
            print("Hallo", e)
            await message.channel.send("I have already joined a voice channel nibba.")


@bot.register_command("fuckoff")
async def command_fuckoff(args, message):
    for x in bot.client.voice_clients:
        if x.guild == message.guild:
            bot.music_player.clear(message)
            return await x.disconnect()


@bot.register_command("queue")
async def command_queue(args, message):
    size = bot.music_player.queue.qsize()

    page = 0
    if len(args) > 0:
        try:
            page = int(args[0])
        except ValueError as e:
            pass

    PAGE_SIZE = 6

    out = "```\nComing up page (%d / %d):\n" % (page, bot.music_player.queue.qsize() / PAGE_SIZE)
    for i in range(page * PAGE_SIZE, min(size, (page + 1) * PAGE_SIZE)):
        _, url, _ = bot.music_player.queue.queue[i]
        song = music_repository.get_song(url)
        out += "%d: %s | %s\n" % (i, song.title, song.owner)
    out += "```"
    await message.channel.send(out)


@bot.register_command("playlist")
async def command_playlist(args, message):
    if len(message.mentions) == 0:
        await message.channel.send("Mention a player to see his playlist.")
        return

    songs = music_repository.get_music(message.mentions[0])

    page = 0
    if len(args) > 0:
        try:
            page = int(args[0])
        except ValueError as e:
            pass

    PAGE_SIZE = 6

    out = "```\nSongs (%d / %d):\n" % (page, len(songs) / PAGE_SIZE)
    for i in range(page * PAGE_SIZE, min(len(songs), (page + 1) * PAGE_SIZE)):
        song = songs[i]
        out += "%d: %s | %s\n" % (i, song.title, song.owner)
    out += "```"
    await message.channel.send(out)


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


@bot.register_command("pause")
async def command_pause(args, message):
    await bot.music_player.pause(message)


@bot.register_command("unpause")
async def command_unpause(args, message):
    await bot.music_player.unpause(message)


@bot.register_command("music")
async def command_music(args, message):
    voice = bot.get_voice_by_guild(message.guild)
    if voice is None:
        await message.channel.send("I am not in a voice channel yet, invite me with !join before playing music.")
        return

    if len(args) < 1:
        return

    try:
        speed = float(args[-1])
    except ValueError as e:
        speed = 1.0

    if args[0] == "all":
        songs = []
        if len(message.mentions) == 0:
            songs = music_repository.get_music()
        else:
            for member in message.mentions:
                songs.extend(music_repository.get_music(member))

        shuffle(songs)
        for song in songs:
            bot.music_player.add_queue(message, song.url, speed, True)

        await message.channel.send("Queueing " + str(len(songs)) + " songs.")
        await message.delete()
    elif is_valid_youtube_url(args[0]):
        url = args[0]
        bot.music_player.add_queue(message, url, speed)
        await message.delete()
    elif args[0] == "search":
        url = bot.youtube_api.search(" ".join(args))
        bot.music_player.add_queue(message, url, speed)
        await message.delete()
    else:
        await message.channel.send("Invalid youtube url. Did you mean !music all @user or !music search <query>?")


@bot.register_command("skip")
async def command_skip(args, message):
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
    if bot.music_player and bot.music_player.is_playing:
        bot.music_player.clear(message)
    await bot.kill()


@bot.register_command("explode")
async def command_explode(args, message):
    """
    !explode <[emote] | [user]>: prints a larger version of the emote, or the user's profile picture.

    Explode pulls the source image for the emote or the original user profile image from the discord servers.
    This gets printed in a code block, and the original message gets removed.

    :param args:
    :param message:
    """
    image = message.content.split(" ")[1]
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
                await message.channel.send((message.author.nick or message.author.name) + ":", embed=em)
                await message.delete()


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


@bot.register_command("report")
async def command_report(args, message: Message):
    """
    !report <show | time | [user tag]>: Contains all interaction with the report functionality.

    Show shows a list counting the reports per user.
    Time shows the time left until a user may report again.
    [user tag] is the to be reported user in the current guild, can be done once per 30 minutes.

    :param args:
    :param message:
    """
    if args[0] == "show":
        out = "```"
        reports = report_repository.get_reports(message.guild)
        for report, n in reports:
            out += "%s %d\n" % (report.reportee, n)
        out += "```"
        await message.channel.send(out)
    elif args[0] == "time":
        reporting = message.author
        time = report_repository.report_allowed(message.guild, reporting)
        if time > 0:
            await message.channel.send("Wait %d minutes to report again." % time)
        else:
            await message.channel.send("You have no report downtime.")
    else:
        if len(message.mentions) == 0:
            await message.channel.send("Tag someone in your message to report them.")
            return

        reportee = message.guild.get_member(message.mentions[0].id)
        reporting = message.author

        # Not allowed to report the bot.
        if message.mentions[0] == "340197681311776768":
            await message.channel.send("I don't think so, bro.")
            reportee = message.author

        time = report_repository.report_allowed(message.guild, reporting)
        if time is None:
            report = Report(message.guild, reportee, reporting)
            report_repository.add_report(report)
        else:
            await message.channel.send("Wait %d minutes to report again." % time)


@bot.register_command("honor")
async def command_report(args, message: Message):
    """
    !honor <show | time | [user tag]>: Contains all interaction with the honor functionality.

    Show shows a list counting the honor per user.
    Time shows the time left until a user may honor again.
    [user tag] is the to be honored user in the current guild, can be done once per 30 minutes.

    :param args:
    :param message:
    """
    if args[0] == "show":
        out = "```"
        honors = honor_repository.get_honors(message.guild)
        for honor, n in honors:
            out += "%s %d\n" % (honor.honoree, n)
        out += "```"
        await message.channel.send(out)
    elif args[0] == "time":
        honoring = message.author
        time = honor_repository.honor_allowed(message.guild, honoring)
        if time > 0:
            await message.channel.send("Wait %d minutes to honor again." % time)
        else:
            await message.channel.send("You have no honor downtime.")
    else:
        uid = args[0].replace("<", "").replace(">", "").replace("@", "").replace("!", "")
        honoree = message.guild.get_member(int(uid))
        honoring = message.author

        if honoring == honoree:
            return

        time = honor_repository.honor_allowed(message.guild, honoring)
        if time is None:
            honor = Honor(message.guild, honoree, honoring)
            honor_repository.add_honor(honor)
        else:
            await message.channel.send("Wait %d minutes to honor again." % time)
