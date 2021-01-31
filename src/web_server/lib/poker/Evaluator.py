from typing import List

from src.web_server.lib.poker.Card import Card


def get_ranks(cards):
    rank_dict = {}
    for card in cards:
        if card.rank in rank_dict:
            rank_dict[card.rank].append(card)
        else:
            rank_dict[card.rank] = [card]
    return rank_dict


def get_suits(cards):
    suits_count = {"HEARTS": [],
                   "DIAMONDS": [],
                   "SPADES": [],
                   "CLUBS": []}

    for card in cards:
        suits_count[card.suit.name].append(card)
    return suits_count


def royal_flush(cards):
    suits_count = get_suits(cards)
    for cards in suits_count.values():

        if len(cards) >= 5:  # Amount of same suit needed for royal flush to be possible
            royal_flush_cards = []
            for card in cards:
                if card.rank.value >= 10:
                    royal_flush_cards.append(card)
            if len(royal_flush_cards) == 5:
                return True, sorted(royal_flush_cards, key=lambda c: c.rank.value, reverse=True)
    return False, None


def straight_flush(cards):
    suits_count = get_suits(cards)
    for suit_cards in suits_count.values():
        if len(suit_cards) >= 5:
            index = -1  # To get highest possible straight flush go from highest to lowest cards
            sorted_cards = sorted(suit_cards, key=lambda c: c.rank.value, reverse=False)

            in_row = [sorted_cards[index]]
            while len(in_row) < 5:
                try:
                    if sorted_cards[index].rank.value - 1 == sorted_cards[index - 1].rank.value:
                        in_row.append(sorted_cards[index - 1])
                    elif sorted_cards[index].rank.value == sorted_cards[index - 1].rank.value:
                        index -= 1
                        continue
                    else:
                        in_row = [sorted_cards[index - 1]]
                    index -= 1
                except IndexError:
                    return False, None
            return True, in_row
    return False, None


def four_kind(cards):
    rank_dict = get_ranks(cards)
    for rank, cards in rank_dict.items():
        sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
        if len(sorted_cards) == 4:
            return True, sorted_cards[0:4]
    return False, None


def full_house(cards):
    match, three_kind_cards = three_kind(cards)
    if not match:
        return False, None
    match, one_pair_cards = one_pair([card for card in cards if card not in three_kind_cards])
    if match:
        return True, three_kind_cards + one_pair_cards
    return False, None


def flush(cards):
    suit_dict = get_suits(cards)
    for suit, cards in suit_dict.items():
        sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
        if len(sorted_cards) >= 5:
            return True, sorted_cards[0:5]
    return False, None


def straight(cards):
    sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=False)
    index = -1
    in_row = [sorted_cards[index]]
    while len(in_row) < 5:
        try:
            if sorted_cards[index].rank.value - 1 == sorted_cards[index - 1].rank.value:
                in_row.append(sorted_cards[index - 1])
            elif sorted_cards[index].rank.value == sorted_cards[index - 1].rank.value:
                index -= 1
                continue
            else:
                in_row = [sorted_cards[index - 1]]
            index -= 1
        except IndexError:
            return False, None
    return True, in_row


def three_kind(cards):
    rank_dict = get_ranks(cards)
    three_kind_cards = None
    for rank, cards in rank_dict.items():
        if len(cards) == 3:
            if three_kind_cards is None:
                three_kind_cards = cards
            elif rank.value > three_kind_cards[0].rank.value:
                three_kind_cards = cards
    return three_kind_cards is not None, three_kind_cards  # TODO: Refactor this


def one_pair(cards):
    rank_dict = get_ranks(cards)
    pair = None
    for rank, cards in rank_dict.items():
        if len(cards) >= 2:
            if pair is None:
                pair = cards
            elif rank.value > pair[0].rank.value:
                pair = cards
    if pair is None:
        return False, None

    return True, pair[0:2]


def highest_card(cards: List[Card]):
    sorted_cards = sorted(cards, key=lambda c: c.rank.value, reverse=True)
    return True, [sorted_cards[0]]
