from discord.ext import commands
from discord.ext.commands import Context

from database import db
from database.models.models import Report, Honor
from database.repository import honor_repository, report_repository
from database.repository.profile_repository import get_profile, get_money


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
                out += "Reported by:\n"
                reports = report_repository.get_all_reports(message.guild, message.mentions[0])
                for report_obj, n in reports:
                    out += "%s %d\n" % (report_obj.reporting, n)
            else:
                reports = report_repository.get_reports(message.guild)
                for report_obj, n in reports:
                    out += "%s %d\n" % (report_obj.reportee, n)
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
            if message.mentions[0] == "340197681311776768":
                await message.channel.send("I don't think so, bro.")
                reportee = message.author

            time = report_repository.report_allowed(message.guild, reporting)
            if time is None:
                report_obj = Report(message.guild, reportee, reporting)
                report_repository.add_report(report_obj)
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
            honors = honor_repository.get_honors(message.guild)
            for honor, n in honors:
                out += "%s %d\n" % (honor.honoree, n)
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
                session = db.session()

                # Add money to balance if honored
                money = get_money(honoree)
                money.balance += 100
                session.commit()

                honor_repository.add_honor(honor)
            else:
                await message.channel.send("Wait %d minutes to honor again." % time)
