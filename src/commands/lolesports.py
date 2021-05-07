from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import Embed
import score_api
from database import db
from database.models.models import Profile, LeagueGame
from database.repository import game_repository


class Esports(commands.Cog):
    BET_MODIFIER = 2

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def ongoing_matches():
        out = "```"
        out += "ID | Match | Status | Winner: \n"
        matches = score_api.get_running_tournament_matches()

        for match_id, match in matches.items():
            out += str(match_id) + "\t" + str(match[0]) + "\t" + str(match[1]) + "\t" + str(match[2]) + "\n"
        out += "```"
        return out

    @staticmethod
    def get_match(match_id):
        match = score_api.get_match_by_id(match_id)
        embed = Embed(title=match.get("name"), url="https://realdrewdata.medium.com/",
                      description=("Winner: " + match.get("winner").get(
                          "acronym")) if match.get("status") == "finished" else "Winner: Undecided",
                      color=0xFF5733)
        embed.set_author(name=match.get("league").get("name") + " - " + match.get("tournament").get("name"),
                         icon_url=match.get("league").get('image_url'))
        embed.set_thumbnail(
            url='https://static.wikia.nocookie.net/leagueoflegends/images/5/53/Riot_Games_logo_icon.png/revision/latest/scale-to-width-down/124?cb=20190417213704')
        return embed

    def bet_match(self, context, session, match_id, bet_team, bet_amount, profile):
        match = score_api.get_match_by_id(match_id)
        if match is None:
            return "Cannot find the match you currently want to bet on"  # TODO
        if match.get("status", None) == "not_started":
            if profile.balance < bet_amount:
                return f"You are betting more than you currently have! (Current balance: {profile.balance})"
            if bet_amount < 0:
                return "You cannot bet a negative amount"
            self.create_league_bet(context, session, match_id, bet_team, bet_amount, profile)
            return f"Successfully created bet of {bet_amount} on {bet_team} to win in the match {match.get('name')}"
        else:
            return "You cannot bet on matched that have finished"

    @commands.command()
    async def esports(self, context: Context, subcommand: str, match_id: str = None, bet_team: str = None,
                      bet_amount: int = None):

        game_repository.remove_game(2)
        message = context.message
        session = db.session()
        profile = session.query(Profile).filter(Profile.discord_id == context.author.id).one_or_none()
        if subcommand == "ongoing":
            await message.channel.send(self.ongoing_matches())

        if subcommand == "match":
            await message.channel.send(embed=self.get_match(match_id))

        if subcommand == "bet":
            await message.channel.send(self.bet_match(context, session, match_id, bet_team, bet_amount, profile))

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

    @tasks.loop(seconds=20)
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
                if score_api.is_game_finished(game.game_id) == "finished":
                    information = self.process_game_result(user, game, session)
                    if information is not None:
                        await self.bot.get_channel(game.channel_id).send("`%s`" % information)
        except Exception as e:
            print(e)

    def process_game_result(self, user, game: LeagueGame, session):
        match = score_api.get_match_by_id(game.game_id)
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
