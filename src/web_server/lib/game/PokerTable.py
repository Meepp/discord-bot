from enum import Enum

from discord import User

from database import db
from database.models.models import Profile
from database.repository import profile_repository
from src.web_server import sio
from src.web_server.lib.game import Evaluator
from src.web_server.lib.game.Exceptions import PokerException
from src.web_server.lib.game.Player import Player
from src.web_server.lib.game.Card import CardSuits, Card, CardRanks
import random
from typing import Optional, List

from web_server.lib.game.PokerSettings import PokerSettings

SMALL_BLIND_CALL_VALUE = 2
MINIMUM_RAISE = 1


class Phases(Enum):
    NOT_YET_STARTED = 0
    PRE_FLOP = 1
    FLOP = 2
    TURN = 3
    RIVER = 4
    POST_ROUND = 5


class HandRanking:
    ROYAL_FLUSH = 0
    STRAIGHT_FLUSH = 1
    FOUR_KIND = 2
    FULL_HOUSE = 3
    FLUSH = 4
    STRAIGHT = 5
    THREE_KIND = 6
    ONE_PAIR = 7
    HIGH_CARD = 8


def deck_generator():
    deck = []

    for suit in [suit for suit in dir(CardSuits) if not suit.startswith("__")]:
        for rank in [rank for rank in dir(CardRanks) if not rank.startswith("__")]:
            deck.append(Card(CardRanks[rank], CardSuits[suit]))

    # TODO: Use a non-crackable shuffle function instead
    random.shuffle(deck)
    return deck


def synchronize_balance(players):
    session = db.session()
    for player in players:
        profile = profile_repository.get_profile(user_id=player.profile.owner_id)
        difference = player.profile.balance - player.initial_balance

        profile.balance += difference
        player.profile = profile

        player.initial_balance = player.profile.balance
    session.commit()


class PokerTable:
    """
    Stores information about the web_server game being played
    """

    def __init__(self, room_id):
        self.room_id = room_id

        self.player_list: List[Player] = []
        self.spectator_list: List[Player] = []
        self.all_in_list: List[Player] = []
        self.fold_list: List[Player] = []
        self.caller_list: List[Player] = []

        self.deck = None
        self.small_blind_index = 0
        self.phase: Phases = Phases.NOT_YET_STARTED
        self.community_cards: List[Card] = []

        self.first = True
        self.pot = 0

        # Create default settings class.
        self.settings = PokerSettings(settings={})

        self.current_call_value = 0
        self.active_player_index = 0
        self.all_in = False

    def initialize_round(self):
        """
        Initializes the Poker game, resets the pot to 0

        :return: An error string, or None if no error occurred.
        """
        # Move all spectating players to the table
        self.player_list.extend(self.spectator_list)
        self.spectator_list = []

        # Get latest balance from server
        for player in self.player_list:
            profile = profile_repository.get_profile(user_id=player.profile.owner_id)
            player.profile = profile
            print("Updating %ss profile" % player.profile.owner)

        # Move all no balance players to spectator list
        for player in self.player_list[:]:
            if player.profile.balance == 0:
                self.player_list.remove(player)
                self.spectator_list.append(player)
            else:
                player.reset()

        while len(self.player_list) > 8:
            player = self.player_list.pop()
            self.spectator_list.append(player)

        for player in self.spectator_list:
            sio.emit("message", "You are a spectator this round.", room=player.socket)

        # Check if there are enough players
        if len(self.player_list) < 2:
            raise PokerException("Need at least two players to start the game.")

        self.small_blind_index %= len(self.player_list)

        # Ensure all players start on equal grounds.
        self.set_player_balances()

        self.deck = deck_generator()
        self.deal_cards()

        self.current_call_value = self.settings.small_blind_value

        self.first = True

        self.fold_list = []
        self.caller_list = []
        self.all_in_list = []

        self.active_player_index = self.small_blind_index
        self.community_cards: List[Card] = []

        self.start_next_phase()

    def broadcast(self, message):
        sio.emit("message", message, room=self.room_id)

    def post_round(self):
        self.small_blind_index = (self.small_blind_index + 1) % len(self.player_list)
        self.caller_list = [player for player in self.player_list if player not in self.fold_list]

        # The game actually finished after all phases
        if len(self.fold_list) != len(self.player_list) - 1:
            hand_scores = {}
            for player in self.caller_list:
                hand_scores[player] = self.evaluate_hand(player.hand)

            winning_players = [self.caller_list[0]]
            for player in self.caller_list[1:]:
                equal = True
                for (_, tier1), (_, tier2) in zip(hand_scores[player], hand_scores[winning_players[0]]):
                    if tier1 < tier2:
                        winning_players = [player]
                        equal = False
                        break
                    if tier1 > tier2:
                        equal = False
                        break

                if equal:
                    for (card1, _), (card2, _) in zip(hand_scores[player], hand_scores[winning_players[0]]):
                        if card1.rank.value > card2.rank.value:
                            winning_players = [player]
                            equal = False
                            break
                        if card1.rank.value < card2.rank.value:
                            equal = False
                            break
                    if equal:
                        winning_players.append(player)
        else:
            winning_players = [self.caller_list[0]]

        shared_pot = self.payout_pot(len(winning_players))

        self.broadcast("%s won." % ",".join([player.profile.owner for player in winning_players]))

        # Payout the game
        for player in winning_players:
            player.payout(shared_pot)

        self.phase = Phases.NOT_YET_STARTED

        # Synchronize profiles with the database
        synchronize_balance(self.player_list)

        self.update_players()

    def get_player(self, profile: Profile, spectator=False):
        combined_list = self.player_list[:]
        if spectator:
            combined_list.extend(self.spectator_list)
        for player in combined_list:
            if player.profile.owner_id == profile.owner_id:
                return player
        return None

    def start_next_phase(self):
        self.phase = Phases(self.phase.value + 1)
        self.broadcast("Starting phase " + self.phase.name.capitalize().replace("_", " "))

        if self.phase == Phases.PRE_FLOP:
            self.first = True
        elif self.phase == Phases.FLOP:
            # Flop deals 3 cards
            self.community_cards.append(self.take_card())
            self.community_cards.append(self.take_card())
            self.community_cards.append(self.take_card())
        elif self.phase == Phases.TURN:
            self.community_cards.append(self.take_card())
        elif self.phase == Phases.RIVER:
            self.community_cards.append(self.take_card())
        elif self.phase == Phases.POST_ROUND:
            self.post_round()

        # If everybody is all in, continue with the next phase immediately, and wait on the last phase
        if self.phase != Phases.NOT_YET_STARTED and len(self.player_list) == len(self.all_in_list):
            self.start_next_phase()

    def round(self, profile: Profile, action: str, value: int = 0):
        if self.phase == Phases.NOT_YET_STARTED or self.phase == Phases.POST_ROUND:
            return "The next round has not yet started."

        if self.get_current_player().profile.id != profile.id:
            return "It is not yet your turn."

        message = None
        player = self.get_current_player()
        if self.first:
            if self.get_small_blind() != player:
                raise ValueError("The small blind was not the first player to do an action.")

            self.first = False
            paid = player.pay(self.current_call_value)  # Current small blind
            if paid != 0:
                self.broadcast("%s started the round with %d." % (player.profile.owner, self.current_call_value))
                self.add_pot(paid)
                self.current_call_value = self.settings.small_blind_value * 2  # In cents
            else:
                raise ValueError("Programmer error: please check the player balances before starting the next round.")

        elif action == "call":
            if player.all_in:
                self.action_call(player, 0)
            else:
                paid = player.pay(self.current_call_value)
                self.action_call(player, paid)

        elif action == "raise":
            difference = player.current_call_value + value - self.current_call_value
            if difference <= 0:
                return "Raise of %d not high enough." % value

            paid = player.pay(self.current_call_value + difference)

            if paid != 0:
                self.add_pot(paid)
                self.current_call_value += difference
                self.caller_list = [player]
                self.broadcast("%s raised by %d." % (player.profile.owner, difference))
            else:
                return "Not enough currency to raise by %d." % value

        elif action == "fold":
            if not self.action_fold(player):
                return None

            message = "Folded."

        self.increment_player()

        self.check_phase_finish()
        return message

    def increment_player(self):
        """
        If this freezes, you did something wrong elsewhere.
        This assumes the fold_list is not the same as all the joined players.
        """
        self.active_player_index = (self.active_player_index + 1) % len(self.player_list)
        if self.get_current_player() in self.fold_list:
            self.increment_player()

    def get_current_player(self):
        return self.player_list[self.active_player_index]

    def deal_cards(self):
        # First round
        for player in self.player_list:
            player.deal(self.take_card())

        for player in self.player_list:
            player.deal(self.take_card())

    def take_card(self) -> Optional[Card]:
        if len(self.deck):
            return self.deck.pop()
        else:
            return None

    def add_player(self, profile: Profile, socket_id):
        for player in self.player_list + self.spectator_list:
            if player.profile.id == profile.id:
                # If the user is already in the list, overwrite the socket id to the newest one.
                player.socket = socket_id
                return

        player = Player(profile, socket_id, self)
        if self.phase == Phases.NOT_YET_STARTED and len(self.player_list) < 8:
            # Store database profile to player list
            self.player_list.append(player)
        else:
            self.spectator_list.append(player)

    def get_small_blind(self):
        return self.player_list[self.small_blind_index]

    def get_big_blind(self):
        return self.player_list[(self.small_blind_index + 1) % len(self.player_list)]

    def add_pot(self, value: int):
        self.pot += value

    def check_phase_finish(self):
        if len(self.player_list) != len(self.fold_list) + len(self.caller_list):
            return False

        self.caller_list = []

        # Start new phase
        self.start_next_phase()

    def export_state(self, player: Player):
        return {
            "you": player.profile.owner,
            "small_blind": self.get_small_blind().profile.owner,
            "current_call_value": self.current_call_value,
            "pot": self.pot,
            "phase": self.phase.name.capitalize(),
            "active_player_index": self.active_player_index,
            "active_player": self.get_current_player().profile.owner,
            "community_cards": [card.to_json() for card in self.community_cards],
            "fold_list": [player.profile.owner for player in self.fold_list],
            "caller_list": [player.profile.owner for player in self.caller_list],
            "spectator_list": [player.profile.owner for player in self.spectator_list],
            "hand": player.export_hand(),
            "players": self.export_player_game_data(),
            "balance": player.profile.balance,
            "to_call": (self.current_call_value - player.current_call_value),
            "started": self.phase != Phases.NOT_YET_STARTED,
            "settings": self.settings.to_json(),
        }

    def evaluate_hand(self, hand: List[Card]):
        all_cards = hand + self.community_cards

        best_cards = []

        evaluators = [
            Evaluator.royal_flush,
            Evaluator.straight_flush,
            Evaluator.four_kind,
            Evaluator.full_house,
            Evaluator.flush,
            Evaluator.straight,
            Evaluator.three_kind,
            Evaluator.one_pair,
            Evaluator.highest_card
        ]

        highest_evaluator = 0
        while len(best_cards) < 5:
            for highest_evaluator in range(highest_evaluator, len(evaluators)):
                match, cards = evaluators[highest_evaluator](all_cards)
                if match:
                    # Remove all matches from all cards list
                    all_cards = [card for card in all_cards if card not in cards]

                    # Add evaluator rank to card
                    result = list(zip(cards, len(cards) * [highest_evaluator]))
                    best_cards.extend(result)
                    if len(best_cards) == 4:  # In case four of a kind with pair
                        highest_evaluator = 8
                    break

        return best_cards[0:5]

    def action_fold(self, player: Player):
        """
        Returns False if the fold made the game finish.

        :param player:
        :return:
        """
        self.fold_list.append(player)
        if len(self.fold_list) == len(self.player_list) - 1:
            # Second to last phase, because phase start increments the phase itself.
            self.phase = Phases.RIVER
            self.start_next_phase()
            return False
        return True

    def action_call(self, player: Player, value):
        self.pot += value
        self.caller_list.append(player)
        self.broadcast("%s called %d." % (player.profile.owner, value))

    def payout_pot(self, shares=1):
        payout_pot = int(self.pot / shares)
        leftover = self.pot - (payout_pot * shares)
        self.pot = leftover
        return payout_pot

    def update_players(self):
        for player in self.player_list + self.spectator_list:
            sio.emit("table_state", self.export_state(player), json=True, room=player.socket)

    def export_player_game_data(self):
        data = []

        for other in self.player_list:
            if other in self.fold_list:
                state = "Folded"
            elif other in self.caller_list:
                state = "Called"
            else:
                state = "Waiting"

            if self.phase == Phases.NOT_YET_STARTED and state != "Folded":
                hand = other.export_hand()
            else:
                hand = None

            data.append({
                "active": self.get_current_player() == other,
                "name": other.profile.owner,
                "state": state,
                "balance": other.profile.balance,
                "hand": hand,
                "ready": other.ready,
            })

        return data

    def cleanup(self):
        for player in self.player_list:
            player.leave()

    def check_readies(self):
        for player in self.player_list:
            if not player.ready:
                return False
        return True

    def remove_player(self, profile: Profile):
        player = self.get_player(profile, spectator=True)
        synchronize_balance([player])

        lists = [self.player_list, self.spectator_list, self.all_in_list, self.fold_list, self.caller_list]
        # Cleanup player from all lists
        for l in lists:
            if player in l:
                l.remove(player)

    def set_player_balances(self):
        for player in self.player_list:
            player.initial_balance = player.profile.balance = min(player.profile.balance, self.settings.max_buy_in)
