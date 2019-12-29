import os
from random import randint, shuffle

import discord
from discord import Message, Guild

from src import bot
from src.database.models.models import Trigger, Report
from src.database.repository import trigger_repository, report_repository


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


@bot.register_command("delete")
async def command_delete(args, message):
    filename = os.path.join(bot.music_player.download_folder, bot.music_player.currently_playing.file)
    bot.music_player.skip(message.guild)
    bot.music_player.deletables.append(filename)


@bot.register_command("pause")
async def command_pause(channel):
    await bot.music_player.pause(channel)


@bot.register_command("unpause")
async def command_unpause(channel):
    await bot.music_player.unpause(channel)


@bot.register_command("music")
async def command_music(args, message):
    if len(args) < 1:
        return

    try:
        speed = float(args[-1])
    except ValueError as e:
        speed = 1.0

    if args[0] == "random":
        # TODO: Pull all music from db
        onlyfiles = []

        shuffle(onlyfiles)
        for file in onlyfiles:
            await bot.music_player.add_queue(message, file, speed, downloaded=True)

        await message.channel.send("Queueing: Everything")
        await message.delete()
    else:
        await bot.music_player.add_queue(message, args[0], speed)
        await message.delete()


@bot.register_command("skip")
async def command_skip(args, message):
    bot.music_player.skip(message.guild)


@bot.register_command("kill")
async def command_kill(args, message):
    if bot.music_player and bot.music_player.is_playing:
        bot.music_player.clear(message)
    await bot.client.logout()


@bot.register_command("explode")
async def command_explode(args, message):
    image = message.content.split(" ")[1:]
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
    out += "{0: <50} | {1: <32} | {2: <16}\n".format("Trigger"[:50], "Response"[:32], "Creator"[:16])
    for trigger in bot.triggers[message.guild]:
        if trigger is None:
            continue
        out += "{0: <50} | {1: <32} | {2: <16}\n".format(trigger.trigger[:50], trigger.response[:32], trigger.author[:16])
    out += "```"
    await message.channel.send(out)


@bot.register_command("help")
async def command_help(args, message):
    help_text = "```Available commands:\n\
  !ree     : Let the bot REEEEEEEEEEEEEEEEEEEEEEEEEEE\n\
  !pubg    : Roept de pubmannen op voor een heerlijk maaltijd kippendinner!\n\
  !roll    : Rol een dobbelsteen, !roll 5 rolt tussen de 0 en de 5\n\
  !join    : De bot joint je voice channel\n\
  !fuckoff : De bot verlaat je v oice channel\n\
  !music   : De bot voegt een youtube filmpje aan de queue (geef een link als argument mee)\n\
  !pause   : Pauzeert het huidige youtube filmpje\n\
  !unpause : Resumes het huidige youtube filmpje\n\
  !joinpub : Met deze commando join je de Pubmannen groep\n\
  !trigger <add|remove|show>: Add or remove trigger words.\n\
  !leavepub: Met deze commando verlaat je de Pubmannen groep\n\
  !skip    : Skipt het huidige youtube filmpje ```"
    await message.channel.send(help_text)


@bot.register_command("report")
async def command_help(args, message: Message):
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
        id = args[0].replace("<", "").replace(">", "").replace("@", "").replace("!", "")
        reportee = message.guild.get_member(int(id))
        reporting = message.author

        time = report_repository.report_allowed(message.guild, reporting)
        if time is None:
            report = Report(message.guild, reportee, reporting)
            report_repository.add_report(report)
        else:
            await message.channel.send("Wait %d minutes to report again." % time)

