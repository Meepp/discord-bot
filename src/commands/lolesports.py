from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import Embed, User
from database import mongodb as db
from database.models.models import Profile, LeagueGame, EsportGame
from database.repository import game_repository, profile_repository
from datetime import datetime, timezone


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
        if match is None:
            return f"No match found with match id: {match_id}", None
        bets = game_repository.get_match_by_id(match_id)
        embed = Embed(title=match.get("name"),
                      description=("Winner: " + match.get("winner").get(
                          "acronym")) if (match.get("status") == "finished" and match.get("winner") is not None)
                      else f"Scheduled at: {self.convert_scheduled_at(match.get('scheduled_at'))}",
                      color=0xFF5733)
        embed.set_author(name=match.get("league").get("name") + " - " + match.get("tournament").get("name"),
                         icon_url=match.get("league").get('image_url'))
        embed.set_thumbnail(url="attachment://match_image.png")
        embed.add_field(name="Official stream:", value=match.get("stream_url"), inline=False)

        blue, odds, red = self.get_odds(match)
        embed.add_field(name="Betting Return", value="%s: %.3f - %s: %.3f" % (blue, odds[0], red, odds[1]), inline=True)
        if len(bets) > 0:
            bets_for_match = ""
            for bet in bets:
                user = self.bot.get_user(bet['owner_id'])
                bets_for_match += f"{user.name}: {bet['amount']} on {bet['team']}\n"
            embed.add_field(name="Active Bets:", value=bets_for_match, inline=False)

        return embed, match.get("image_file")

    def get_odds(self, match):
        teams = match.get("opponents")
        blue, red = teams[0].get("opponent").get("name"), teams[1].get("opponent").get("name")
        odds = self.bot.predictor.synchronized_compute_prediction(blue, red)
        if odds is None:
            odds = (2, 2)  # Default odds in case teams are not found
        return blue, odds, red

    def bet_match(self, context, match_id, bet_team, bet_amount):
        profile = profile_repository.get_profile(user_id=context.author.id)
        match = self.panda_score_api.get_match_by_id(match_id)
        if match is None:
            return f"No match found with match id: {match_id}"
        if not isinstance(bet_amount, int):
            return f"Please bet an integer amount between 1 and {profile['balance']}"

        if match.get("status") == "not_started":
            if profile['balance'] < bet_amount:
                return f"You are betting more than you currently have! (Current balance: {profile['balance']})"
            if bet_amount < 0:
                return "You cannot bet a negative amount"
            bet_team = bet_team.upper()
            if bet_team in match.get("name"):
                blue, odds, red = self.get_odds(match)
                if match.get("opponents")[0]['opponent'].get("acronym") == bet_team:
                    odd = odds[0]
                else:
                    odd = odds[1]
                self.create_league_bet(context, match_id, bet_team, bet_amount, odd, profile)
                return f"Successfully created bet of {bet_amount} on {bet_team} to win in the match {match.get('name')}"
            else:
                return f"You cannot bet on {bet_team} in the match {match.get('name')}."
        else:
            return "You cannot bet on matches that have finished or are currently ongoing"

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

        if subcommand == "ongoing":
            await message.channel.send(self.ongoing_matches())

        elif subcommand == "match":
            match, file = self.get_match(arg_id)
            if isinstance(match, str):
                await message.channel.send(match)
            else:
                await message.channel.send(embed=match, file=file)

        elif subcommand == "bet":
            await message.channel.send(self.bet_match(context, arg_id, bet_team, bet_amount))

        elif subcommand == "team":
            returned_team = self.get_team(arg_id)
            if isinstance(returned_team, Embed):
                await message.channel.send(embed=returned_team)
            else:
                await message.channel.send(returned_team)
        elif subcommand == "upcoming":
            await message.channel.send(embed=self.get_upcoming_matches(arg_id))
        else:
            await message.channel.send(f"Unknown command detected, please see !help esports for correct usage.")

    @staticmethod
    def create_league_bet(context, match_id, bet_team, bet_amount, odd, profile):
        collection = db['esportGame']

        # TODO insert odds for team
        game = EsportGame(context.author, match_id, bet_amount, bet_team.upper(), odd, context.channel.id)
        profile_repository.update_money(profile, -bet_amount)
        collection.insert(game.to_mongodb())

    @tasks.loop(seconds=300)
    async def payout_league_bet(self):
        await self.bot.wait_until_ready()
        collection = db['esportGame']
        games = list(collection.find())
        try:
            for game in games:
                user = self.bot.get_user(game['owner_id'])
                if user is None:
                    print("User id %s not found." % game['owner_id'])
                    continue
                if self.panda_score_api.is_game_finished(game['game_id']) == "finished":
                    information = self.process_game_result(user, game)
                    if information is not None:
                        await self.bot.get_channel(game['channel_id']).send("`%s`" % information)
        except Exception as e:
            print(e)

    def process_game_result(self, user: User, game: dict):
        match = self.panda_score_api.get_match_by_id(game['game_id'])
        if match is None:
            return f"No match found with match id: {game['game_id']}"
        profile = profile_repository.get_profile(user_id=user.id)
        if match.get('winner').get('acronym').upper() == game['team'].upper():
            winnings = round(game['amount'] * game['odds'], 2)
            profile = profile_repository.update_money(profile, winnings)
            information = f"{profile['owner']} won {winnings} on the bet {match.get('name')}"
        else:
            information = f"{profile['owner']} lost {game['amount']} on the bet {match.get('name')}"
        collection = db['esportGame']
        collection.find_one_and_delete({"_id": game['_id']})

        return information

    def get_team(self, arg_id):
        if arg_id.isnumeric():
            teams = self.panda_score_api.get_team_by_id(arg_id)
            if len(teams) == 0:
                return f"Could not find a team with id {arg_id}"
        else:
            teams = self.panda_score_api.get_team_by_acronym(arg_id)
            if len(teams) == 0:
                return f"Could not find a team with acronym {arg_id}"
            if len(teams) > 1:
                list_of_teams = "```"
                for t in teams:
                    list_of_teams += f"{t.get('id')}: {t.get('name')}\n"
                list_of_teams += "```"
                return "There are multiple teams with this acronym, which one did you mean? Type !esports <team_id>\n" + list_of_teams
        team = teams[0]
        embed = Embed(title=team.get("name", ""), color=0xFF5733)
        embed.set_author(name=str(team.get("acronym")) + " - " + str(team.get("location")))
        embed.set_thumbnail(
            url=team.get('image_url'))
        player_list = ""
        for player in team.get('players'):
            player_list += str(player.get('first_name')) + ", " + f"**{player.get('name')}**" + ", " + str(player.get(
                "last_name")) + f" ({player.get('role')})" "\n"
        embed.add_field(name="Player Roster", value=player_list, inline=False)

        return embed

    def get_upcoming_matches(self, league):
        matches = self.panda_score_api.get_upcoming_matches(league)

        match_list = ""
        for match in matches:
            scheduled_at = self.convert_scheduled_at(match.get("scheduled_at"))
            match_list += scheduled_at + " " + str(match.get("id")) + " - " + match.get(
                "name") + "\n"

        embed = Embed(title="Upcoming matches", color=0xFF5733, description=match_list)

        return embed

    @staticmethod
    def convert_scheduled_at(time):
        scheduled_at = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc).astimezone(tz=None)
        if scheduled_at.day == datetime.today().day:
            return f"Today at {scheduled_at.strftime('%H:%M')}"
        else:
            return scheduled_at.strftime("%d/%m/%Y, %H:%M")