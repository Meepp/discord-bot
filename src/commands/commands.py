import os
import queue
import re
from random import randint, shuffle

import discord
from discord import Message, Guild

from src import bot
from src.custom_emoji import CustomEmoji
from src.database.models.models import Trigger, Report, Honor
from src.database.repository import trigger_repository, report_repository, music_repository, honor_repository
from src.database.repository.music_repository import remove_from_owner


def is_valid_youtube_url(input):
    return re.match(r"(http(s)?://)?(www\.)?(youtube\.com|youtu\.be)/.*$", input)


@bot.register_command("roll")
async def command_roll(args, message):
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


@bot.register_command("join")
async def command_join(args, message):
    """
    !join: lets the bot join the voice channel of the person who requested.
    :param args:
    :param message:
    :return:
    """
    if message.author.voice is not None:
        try:
            await message.author.voice.channel.connect()
        except discord.ClientException as e:
            await message.channel.send("I have already joined a voice channel nibba.")
    else:
        await message.channel.send("You are not in a voice channel.")


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


@bot.register_command("pause")
async def command_pause(args, message):
    """
    !pause: pause the currently playing song

    :param args:
    :param message:
    :return:
    """
    await bot.music_player.pause(message)


@bot.register_command("unpause")
async def command_unpause(args, message):
    """
    !unpause: unpause the currently playing song

    :param args:
    :param message:
    :return:
    """
    await bot.music_player.unpause(message)


@bot.register_command("music")
async def command_music(args, message):
    """
    !music (search <query> | all <user(s)> | <youtube url> | playlist <user> <playlist id(s))

    !music all <user> => play all songs in <user>'s playlist
    !music <youtube url> => download song and play
    !music playlist <user> <playlist id(s)> => pick specific songs from playlist

    :param args:
    :param message:
    :return:
    """
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
            await bot.music_player.add_queue(message, song.url, speed)

        await message.channel.send("Queueing " + str(len(songs)) + " songs.")
        await message.delete()
    elif args[0] == "playlist":
        if len(message.mentions) == 0:
            await message.channel.send("No players playlist selected.")
            await message.delete()
            return
            
        member = message.mentions[0]
        
        songs = music_repository.get_music(member)
        nums = []

        for arg in args[1:]:
            try:
                if ":" in arg:
                    data = arg.split(":", 1)
                    low, upp = int(data[0]), int(data[1])
                    nums.extend(n for n in range(max(low, 0), min(upp + 1, len(songs))))
                else:
                    nums.append(int(arg))
            except ValueError as e:
                pass
        
        err = False
        for num in nums:
            if num >= len(songs) or num < 0:
                if not err:
                    await message.channel.send("Playlist id should be between %d and %d" % (0, len(songs)))
                continue

            await bot.music_player.add_queue(message, songs[num].url, 1)
        
        await message.channel.send("Added %d songs" % len([num for num in nums if len(songs) > num >= 0]))
        await message.delete()
    elif args[0] == "search":
        url = bot.youtube_api.search(" ".join(args))
        await bot.music_player.add_queue(message, url, speed)
        await message.delete()
    elif args[0] == "like":
        query = " ".join(args[1:])
        songs = music_repository.query_song_title(query)
        if len(songs) == 0:
            msg = "No songs found."
        else:
            for song in songs:
                await bot.music_player.add_queue(message, song.url, 1)
            msg = "Added %d songs. (First up: %s)" % (len(songs), songs[0].title)
        await message.channel.send(msg)
        await message.delete()
    else:
        url = args[0]
        await bot.music_player.add_queue(message, url, speed)
        await message.delete()


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
        for member in message.mentions:
            url = member.avatar_url_as(size=512)
            em = discord.Embed()
            em.set_image(url=str(url))
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
        if len(message.mentions) > 0:
            out += "Reported by:\n"
            reports = report_repository.get_all_reports(message.guild, message.mentions[0])
            for report, n in reports:
                out += "%s %d\n" % (report.reporting, n)
        else:
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
