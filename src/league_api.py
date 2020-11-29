import requests
from discord import User
from discord.ext import commands, tasks
from discord.ext.commands import Context

from database import db
from database.models.models import Game, Profile
from database.repository import game_repository
from database.repository.profile_repository import get_money

API_URL = "https://euw1.api.riotgames.com"

CONDITIONS = [("dragon", 2), ("baron", 2), ("win", 2), ("herald", 2), ("tower", 2), ("inhibitor", 2)]


class LeagueAPI(commands.Cog):
    def __init__(self, bot, key):
        self.bot = bot
        self.headers = {
            "X-Riot-Token": key
        }

    def get_account_id(self, username: str):
        endpoint = "/lol/summoner/v4/summoners/by-name/%s" % username
        raw_response = requests.get(API_URL + endpoint, headers=self.headers)

        if raw_response.status_code == 200:
            return raw_response.json().get("id")
        else:
            return None

    def set_active_game(self, user: User, summoner_id: str, game: Game):
        endpoint = "/lol/spectator/v4/active-games/by-summoner/%s" % summoner_id
        raw_response = requests.get(API_URL + endpoint, headers=self.headers)

        if raw_response.status_code == 200:
            response = raw_response.json()
            team = None
            game_id = response.get("gameId")
            for participant in response.get("participants"):
                if participant.get("summonerId") == summoner_id:
                    team = participant.get("teamId")

            # Add game to db
            game.team = team
            game.game_id = game_id

            session = db.session()
            session.add(game)
            session.commit()
        else:
            return None

    def process_game_result(self, user, game_id):
        endpoint = "/lol/match/v4/matches/%s" % game_id
        raw_response = requests.get(API_URL + endpoint, headers=self.headers)

        session = db.session()
        game = game_repository.get_game(user, game_id)

        if raw_response.status_code == 200:
            response = raw_response.json()
            teams = response.get("teams")
            information = None

            rate = [x for x in CONDITIONS if x[0] == game.type][0]

            for team in teams:
                if team.get("teamId") == game.team:
                    if (rate[0] == "win" and team.get("win") == "Win") or \
                       (rate[0] == "baron" and team.get("firstBaron")) or \
                       (rate[0] == "herald" and team.get("firstRiftHerald")) or \
                       (rate[0] == "tower" and team.get("firstTower")) or \
                       (rate[0] == "inhibitor" and team.get("firstInhibitor")) or \
                       (rate[0] == "dragon" and team.get("firstDragon")):
                        profile = session.query(Profile).filter(Profile.owner_id == user.id).one_or_none()
                        winnings = game.bet * 2

                        # Find rate from tuple
                        profile.balance += winnings * rate[1]

                        information = "%s won %d!" % (user.name, winnings)
                    else:
                        information = "%s lost the bet on %s of %d." % (user.name, game.type, game.bet)

                    # Remove entry
                    session.delete(game)
                    session.commit()

            return information
        else:
            return None

    @tasks.loop(seconds=120)
    async def payout_games(self):
        await self.bot.wait_until_ready()

        session = db.session()
        games = session.query(Game).all()

        try:
            for game in games:
                user = self.bot.get_user(game.owner_id)
                if user is None:
                    print("User id %d not found." % game.owner_id)
                    continue
                if game.game_id is not None:
                    # The game is in progress if this is the case
                    information = self.process_game_result(user, game.game_id)
                    if information is not None:
                        await self.bot.get_channel(game.channel_id).send("`%s`" % information)
                else:
                    # Fetch active game and set game data
                    profile = session.query(Profile).filter(Profile.owner_id == user.id).one_or_none()
                    self.set_active_game(user, profile.league_user_id, game)

        except Exception as e:
            print(e)

    @commands.command()
    async def bet(self, context: Context, condition: str, amount: int):
        """
        Bet on the next league game you will play.
        """

        session = db.session()
        profile = session.query(Profile).filter(Profile.owner_id == context.author.id).one_or_none()
        if profile.league_user_id is None:
            return await context.channel.send("You dont have a league account linked yet. Set this account using !connect <summonername>")

        if profile.balance < amount:
            return await context.channel.send("You dont have the currency to place this bet.")

        if filter(lambda x: x[0] == condition, CONDITIONS) is None:
            return await context.channel.send("This is not a valid condition.")

        # Create a game object to keep track of bets.
        game = Game(context.author)
        game.bet = amount
        game.type = condition
        game.channel_id = context.channel.id
        profile.balance -= amount
        session.add(game)
        session.commit()

        await context.channel.send("You bet %d to get first %s the next game." % (amount, condition))

    @commands.command()
    async def connect(self, context: Context, name: str):
        """
        Connects your league account to the profile used by this bot.
        Only works on EUW server right now.
        """
        session = db.session()
        profile = session.query(Profile).filter(Profile.owner_id == context.author.id).one_or_none()

        if profile is None:
            profile = Profile(context.author)
            profile.init_balance(session, context.author)
            session.add(profile)

        account_id = self.get_account_id(name)
        if account_id is None:
            return await context.channel.send("This summoner name does not seem to exist.")

        profile.league_user_id = account_id
        session.commit()

        await context.channel.send("Successfully linked %s to your account." % name)
