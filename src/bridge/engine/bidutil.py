"""Shared bidding utility functions.

Pure helpers for bid arithmetic and hand evaluation that are
reusable across bidding systems and auction phases.
"""

from bridge.engine.context import BiddingContext
from bridge.model.bid import SuitBid
from bridge.model.card import Suit


def cheapest_bid_in_suit(suit: Suit, above: SuitBid) -> SuitBid | None:
    """Return the cheapest legal bid in the given suit above the given bid.

    Returns None if no legal bid exists (e.g., trying to bid diamonds
    above 7H -- there is no 8-level).
    """
    for level in range(1, 8):
        candidate = SuitBid(level, suit)
        if candidate > above:
            return candidate
    return None


def suit_hcp(ctx: BiddingContext, suit: Suit) -> int:
    """Sum of HCP in a single suit."""
    return sum(c.rank.hcp for c in ctx.hand.suit_cards(suit))
