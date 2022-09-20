from discord.ext import commands
from discord.ext.commands import Context

from src.database.models.models import Honor, Report
from src.database.repository import honor_repository, report_repository, profile_repository


class Reputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def report(self, context: Context, subcommand: str):
        """
        !report show

        !report <show | time | [user tag]>: Contains all interaction with the report functionality.

        Show shows a list counting the reports per user.
        Time shows the time left until a user may report again.
        [user tag] is the to be reported user in the current guild, can be done once per 30 minutes.
        """
        message = context.message
        if subcommand == "show":
            out = "```"
            if len(message.mentions) > 0:
                pass  # TODO
                # out += "Reported by:\n"
                # reports = report_repository.get_all_reports(message.mentions[0])
                # print(reports)
                # for report in reports:
                #     out += "%s %d\n" % (report['_id'], report['count'])
            else:
                reports = report_repository.get_reports()
                for key,value in reports.items():
                    out += "%s %d\n" % (key, value)
            out += "```"
            await message.channel.send(out)
        elif subcommand == "time":
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
            if message.mentions[0].id == 340197681311776768 or message.mentions[0].id == 772902827633934376:
                await message.channel.send("I don't think so, bro.")
                reportee = message.author

            time = report_repository.report_allowed(message.guild, reporting)
            if time is None:
                report_obj = Report(message.guild, reportee, reporting)
                report_repository.add_report(report_obj)
                profile = profile_repository.get_profile(user_id=reportee.id)
                profile_repository.update_money(profile, -1)
                await message.channel.send(f"{profile['owner']} has been reported and lost 1.")
            else:
                await message.channel.send("Wait %d minutes to report again." % time)

    @commands.command()
    async def honor(self, context: Context, subcommand: str):
        """
        !honor <show | time | [user tag]>: Contains all interaction with the honor functionality.

        Show shows a list counting the honor per user.
        Time shows the time left until a user may honor again.
        [user tag] is the to be honored user in the current guild, can be done once per 30 minutes.
        """
        message = context.message
        if subcommand == "show":
            out = "```"
            honors = honor_repository.get_honors()
            if honors is None:
                return
            for honor in honors:
                out += "%s %d\n" % (honor['_id'], honor['count'])
            out += "```"
            await message.channel.send(out)

        elif subcommand == "time":
            honoring = message.author
            time = honor_repository.honor_allowed(message.guild, honoring)
            if time > 0:
                await message.channel.send("Wait %d minutes to honor again." % time)
            else:
                await message.channel.send("You have no honor downtime.")
        else:
            honoree = message.mentions[0]
            honoring = message.author

            if honoring == honoree:
                return

            time = honor_repository.honor_allowed(message.guild, honoring)
            if time is None:
                honor = Honor(message.guild, honoree, honoring)
                # Add money to balance if honored
                honor_repository.add_honor(honor)
                profile = profile_repository.get_profile(user_id=honoree.id)
                profile_repository.update_money(profile, 100)
                if honoree.id == 772902827633934376 or honoree.id == 340197681311776768:
                    await message.channel.send("Thank you for honoring the hard working bot!")
            else:
                await message.channel.send("Wait %d minutes to honor again." % time)
