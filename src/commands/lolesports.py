from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import Embed
from database import db
from database.models.models import Profile, LeagueGame
from database.repository import game_repository
from datetime import datetime


class Esports(commands.Cog):
    BET_MODIFIER = 2

    def __init__(self, bot, panda_score_api):
        self.bot = bot
        self.panda_score_api = panda_score_api

    def ongoing_matches(self):
        out = "```"
        out += "ID | Match | Status | Winner: \n"
        matches = self.panda_score_api.get_running_tournament_matches()

        for match_id, match in matches.items():
            out += str(match_id) + "\t" + str(match[0]) + "\t" + str(match[1]) + "\t" + str(match[2]) + "\n"
        out += "```"
        return out

    def get_match(self, match_id):
        match = self.panda_score_api.get_match_by_id(match_id)
        bets = game_repository.get_games(int(match_id))
        embed = Embed(title=match.get("name"),
                      description=("Winner: " + match.get("winner").get(
                          "acronym")) if match.get("status") == "finished"
                      else f"Scheduled at: {self.convert_scheduled_at(match.get('scheduled_at'))}",
                      color=0xFF5733)
        embed.set_author(name=match.get("league").get("name") + " - " + match.get("tournament").get("name"),
                         icon_url=match.get("league").get('image_url'))
        embed.set_thumbnail(
            url="attachment://match_image.png")
        embed.add_field(name="Official stream:", value=match.get("stream_url"), inline=False)
        if len(bets) > 0:
            bets_for_match = ""
            for bet in bets:
                user = self.bot.get_user(int(bet.owner_id))
                bets_for_match += f"{user.name}: {bet.bet} on {bet.type}\n"
            embed.add_field(name="Active Bets:", value=bets_for_match, inline=False)

        return embed, match.get("image_file")

    def bet_match(self, context, session, match_id, bet_team, bet_amount, profile):
        match = self.panda_score_api.get_match_by_id(match_id)
        bet_team = bet_team.upper()
        if match is None:
            return "Cannot find the match you currently want to bet on"  # TODO
        if match.get("status", None) == "not_started":
            if profile.balance < bet_amount:
                return f"You are betting more than you currently have! (Current balance: {profile.balance})"
            if bet_amount < 0:
                return "You cannot bet a negative amount"
            match = self.panda_score_api.get_match_by_id(match_id)
            if bet_team in match.get("name"):
                self.create_league_bet(context, session, match_id, bet_team, bet_amount, profile)
                return f"Successfully created bet of {bet_amount} on {bet_team} to win in the match {match.get('name')}"
            else:
                return f"You cannot bet on {bet_team} in the match {match.get('name')}."
        else:
            return "You cannot bet on matches that have finished"

    @commands.command()
    async def esports(self, context: Context, subcommand: str, arg_id: str = None, bet_team: str = None,
                      bet_amount: int = None):
        """
        :param subcommand: Possible options: ongoing, match, bet, team, and upcoming
        :param arg_id: Possible options in case of match or bet: id of match. In case of team: acronym or team id.
        :param bet_team: Acronym of the team you wish to bet on
        :param bet_amount: Amount you wish to bet on the match
        """

        message = context.message
        session = db.session()
        profile = session.query(Profile).filter(Profile.discord_id == context.author.id).one_or_none()
        if subcommand == "ongoing":
            await message.channel.send(self.ongoing_matches())

        elif subcommand == "match":
            embed, file = self.get_match(arg_id)
            await message.channel.send(embed=embed, file=file)

        elif subcommand == "bet":
            await message.channel.send(self.bet_match(context, session, arg_id, bet_team, bet_amount, profile))

        elif subcommand == "team":
            await message.channel.send(embed=self.get_team(arg_id))

        elif subcommand == "upcoming":
            await message.channel.send(embed=self.get_upcoming_matches())
        else:
            await message.channel.send(f"Unknown command detected, please see !help esports for correct usage.")

    @staticmethod
    def create_league_bet(context, session, match_id, bet_team, bet_amount, profile):
        game = LeagueGame(context.author)
        game.game_id = match_id
        game.bet = bet_amount
        game.type = bet_team.upper()
        game.channel_id = context.channel.id
        profile.balance -= bet_amount
        session.add(game)
        session.commit()

    @tasks.loop(seconds=300)
    async def payout_league_bet(self):
        await self.bot.wait_until_ready()

        session = db.session()
        games = session.query(LeagueGame).all()
        try:
            for game in games:
                user = self.bot.get_user(int(game.owner_id))
                if user is None:
                    print("User id %s not found." % game.owner_id)
                    continue
                if self.panda_score_api.is_game_finished(game.game_id) == "finished":
                    information = self.process_game_result(user, game, session)
                    if information is not None:
                        await self.bot.get_channel(game.channel_id).send("`%s`" % information)
        except Exception as e:
            print(e)

    def process_game_result(self, user, game: LeagueGame, session):
        match = self.panda_score_api.get_match_by_id(game.game_id)
        profile = session.query(Profile).filter(Profile.discord_id == user.id).one_or_none()
        if match.get('winner').get('acronym').upper() == game.type.upper():
            winnings = game.bet * self.BET_MODIFIER
            profile.balance += winnings
            information = f"{profile.discord_username} won {winnings} on the bet {match.get('name')}"
        else:
            information = f"{profile.discord_username} lost {game.bet} on the bet {match.get('name')}"
        session.delete(game)
        session.commit()

        return information

    def get_team(self, arg_id):
        if arg_id.isnumeric():
            team = self.panda_score_api.get_team_by_id(arg_id)
        else:
            team = self.panda_score_api.get_team_by_acronym(arg_id)
        embed = Embed(title=team.get("name"), color=0xFF5733)
        embed.set_author(name=team.get("acronym") + " - " + team.get("location"))
        embed.set_thumbnail(
            url=team.get('image_url'))
        player_list = ""
        for player in team.get('players'):
            player_list += player.get('first_name') + ", " + f"**{player.get('name')}**" + ", " + player.get(
                "last_name") + f" ({player.get('role')})" "\n"
        embed.add_field(name="Player Roster", value=player_list, inline=False)

        return embed

    def get_upcoming_matches(self):
        matches = self.panda_score_api.get_upcoming_matches()

        match_list = ""
        for match in matches:
            scheduled_at = self.convert_scheduled_at(match.get("original_scheduled_at"))
            match_list += scheduled_at + " " + str(match.get("id")) + " - " + match.get(
                "name") + "\n"

        embed = Embed(title="Upcoming matches", color=0xFF5733, description=match_list)

        return embed

    @staticmethod
    def convert_scheduled_at(time):
        scheduled_at = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        return scheduled_at.strftime("%m/%d/%Y, %H:%M")
