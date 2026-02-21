"""Hand evaluation functions for bridge bidding.

Pure functions that compute standard bridge metrics from a Hand:
HCP, distribution/length points, quick tricks, losing trick count, controls,
suit quality, suit selection, and opening-bid qualification helpers.
"""

from bridge.model.card import SUITS_SHDC, Rank, Suit
from bridge.model.hand import Hand

_TOP_HONORS = (Rank.ACE, Rank.KING, Rank.QUEEN)
_TOP_5_HONORS = (Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK, Rank.TEN)


def hcp(hand: Hand) -> int:
    """Sum of 4-3-2-1 high card points across all 13 cards."""
    return sum(card.rank.hcp for card in hand.cards)


def length_points(hand: Hand) -> int:
    """Points for long suits: +1 per card beyond the 4th."""
    return sum(max(0, hand.suit_length(suit) - 4) for suit in SUITS_SHDC)


def total_points(hand: Hand) -> int:
    """HCP + length points. Standard combined metric for opening decisions."""
    return hcp(hand) + length_points(hand)


def distribution_points(hand: Hand, trump_suit: Suit | None = None) -> int:
    """Shortness points: void=5, singleton=3, doubleton=1.

    Used when raising partner's suit (dummy valuation).
    If trump_suit is given, shortness in that suit is not counted.
    """
    total = 0
    for suit in SUITS_SHDC:
        if suit == trump_suit:
            continue
        length = hand.suit_length(suit)
        if length == 0:
            total += 5
        elif length == 1:
            total += 3
        elif length == 2:
            total += 1
    return total


def controls(hand: Hand) -> int:
    """Control count: A=2, K=1. Used for slam evaluation."""
    total = 0
    for card in hand.cards:
        if card.rank == Rank.ACE:
            total += 2
        elif card.rank == Rank.KING:
            total += 1
    return total


def quick_tricks(hand: Hand) -> float:
    """Quick tricks per suit, summed. Returns float (0.5 increments).

    Per suit (checked in priority order):
    AK=2.0, AQ=1.5, A=1.0, KQ=1.0, Kx(length>=2)=0.5.
    """
    total = 0.0
    for suit in SUITS_SHDC:
        has_a = hand.has_card(suit, Rank.ACE)
        has_k = hand.has_card(suit, Rank.KING)
        has_q = hand.has_card(suit, Rank.QUEEN)

        if has_a and has_k:
            total += 2.0
        elif has_a and has_q:
            total += 1.5
        elif has_a or (has_k and has_q):
            total += 1.0
        elif has_k and hand.suit_length(suit) >= 2:
            total += 0.5
    return total


def losing_trick_count(hand: Hand) -> int:
    """Losing Trick Count: examine top 3 cards per suit.

    Void=0, singleton A=0 else 1, doubleton AK=0 (A or K)=1 else 2,
    3+ cards: 3 minus number of A/K/Q present.
    """
    total = 0
    for suit in SUITS_SHDC:
        length = hand.suit_length(suit)
        if length == 0:
            continue

        has_a = hand.has_card(suit, Rank.ACE)
        has_k = hand.has_card(suit, Rank.KING)
        has_q = hand.has_card(suit, Rank.QUEEN)

        if length == 1:
            total += 0 if has_a else 1
        elif length == 2:
            if has_a and has_k:
                total += 0
            elif has_a or has_k:
                total += 1
            else:
                total += 2
        else:
            losers = 3
            if has_a:
                losers -= 1
            if has_k:
                losers -= 1
            if has_q:
                losers -= 1
            total += losers
    return total


def quality_suit(hand: Hand, suit: Suit) -> bool:
    """Whether a suit has reasonable quality for a weak two or preempt.

    Requires 2 of {A, K, Q} or 3 of {A, K, Q, J, T}.
    """
    top_3 = sum(1 for r in _TOP_HONORS if hand.has_card(suit, r))
    if top_3 >= 2:
        return True
    top_5 = sum(1 for r in _TOP_5_HONORS if hand.has_card(suit, r))
    return top_5 >= 3


def best_major(hand: Hand) -> Suit | None:
    """Longest 5+ card major, or None. Spades wins ties."""
    s_len = hand.suit_length(Suit.SPADES)
    h_len = hand.suit_length(Suit.HEARTS)
    if s_len < 5 and h_len < 5:
        return None
    if s_len >= h_len:
        return Suit.SPADES
    return Suit.HEARTS


def best_minor(hand: Hand) -> Suit:
    """Minor suit to open per SAYC rules.

    - Longer minor wins.
    - 4-4 in minors: open 1D.
    - 3-3 in minors: open 1C.
    """
    d_len = hand.suit_length(Suit.DIAMONDS)
    c_len = hand.suit_length(Suit.CLUBS)
    if d_len > c_len:
        return Suit.DIAMONDS
    if c_len > d_len:
        return Suit.CLUBS
    # Equal length: 4-4 → 1D, 3-3 → 1C
    if d_len >= 4:
        return Suit.DIAMONDS
    return Suit.CLUBS


def has_outside_four_card_major(hand: Hand, exclude: Suit) -> bool:
    """Whether the hand has a 4+ card major other than the excluded suit."""
    for suit in (Suit.SPADES, Suit.HEARTS):
        if suit != exclude and hand.suit_length(suit) >= 4:
            return True
    return False


def rule_of_20(hand: Hand, hand_hcp: int) -> bool:
    """Rule of 20: HCP + lengths of two longest suits >= 20."""
    lengths = sorted(hand.shape, reverse=True)
    return hand_hcp + lengths[0] + lengths[1] >= 20


def rule_of_15(hand: Hand, hand_hcp: int) -> bool:
    """Rule of 15 (4th seat): HCP + number of spades >= 15."""
    return hand_hcp + hand.suit_length(Suit.SPADES) >= 15
