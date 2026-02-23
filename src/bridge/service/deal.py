"""Random deal generator for bridge."""

from __future__ import annotations

import random

from bridge.model.auction import Seat
from bridge.model.card import SUITS_SHDC, Card, Rank
from bridge.model.hand import Hand


def deal(rng: random.Random | None = None) -> dict[Seat, Hand]:
    """Deal 52 cards into 4 hands of 13.

    Args:
        rng: Optional random.Random instance for reproducible deals.
             If None, uses the default random module.

    Returns:
        Dict mapping each Seat to a Hand.
    """
    deck = [Card(suit, rank) for suit in SUITS_SHDC for rank in Rank]
    if rng is not None:
        rng.shuffle(deck)
    else:
        random.shuffle(deck)

    seats = [Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST]
    return {
        seat: Hand(frozenset(deck[i * 13 : (i + 1) * 13]))
        for i, seat in enumerate(seats)
    }
