"""BiddingContext — pre-computed bundle for rule evaluation."""

from __future__ import annotations

from bridge import evaluate
from bridge.model.auction import AuctionState, Seat, Vulnerability
from bridge.model.bid import Bid, is_pass
from bridge.model.board import Board
from bridge.model.card import Suit
from bridge.model.hand import Hand


class AuctionContext:
    """Auction-derived context -- no hand required.

    Contains everything derivable from the auction state and seat alone.
    Used by ``possible_bids()``, ``promises()``, and prerequisites, which
    never access hand data.  For full hand evaluation, use ``BiddingContext``.
    """

    def __init__(self, auction: AuctionState, seat: Seat) -> None:
        my_non_pass = tuple(b for b in auction.bids_by(seat) if not is_pass(b))

        self.seat: Seat = seat
        self.auction: AuctionState = auction
        self.vulnerability: Vulnerability = auction.vulnerability

        self.has_opened: bool = auction.has_opened
        self.opening_bid: tuple[Seat, Bid] | None = auction.opening_bid
        self.partner_last_bid: Bid | None = auction.partner_last_bid(seat)
        self.rho_last_bid: Bid | None = auction.rho_last_bid(seat)
        self.is_competitive: bool = auction.is_competitive()
        self.my_bids: tuple[Bid, ...] = my_non_pass
        self.is_my_first_bid: bool = len(my_non_pass) == 0
        self.is_vulnerable: bool = auction.vulnerability.is_vulnerable(seat)


class BiddingContext(AuctionContext):
    """Everything a rule needs to make a decision.

    Extends ``AuctionContext`` with hand metrics and shape helpers.
    Built once per advise() call from a Board, then passed to every rule.
    """

    def __init__(self, board: Board) -> None:
        super().__init__(board.auction, board.seat)

        hand = board.hand

        # Hand
        self.hand: Hand = hand

        # Pre-computed hand metrics
        self.hcp: int = evaluate.hcp(hand)
        self.length_pts: int = evaluate.length_points(hand)
        self.total_pts: int = evaluate.total_points(hand)
        self.distribution_pts: int = evaluate.distribution_points(hand)
        self.controls: int = evaluate.controls(hand)
        self.quick_tricks: float = evaluate.quick_tricks(hand)
        self.losers: int = evaluate.losing_trick_count(hand)

        # Shape helpers
        self.shape: tuple[int, int, int, int] = hand.shape
        self.sorted_shape: tuple[int, ...] = hand.sorted_shape
        self.is_balanced: bool = hand.is_balanced
        self.is_semi_balanced: bool = hand.is_semi_balanced
        self.longest_suit: Suit = hand.longest_suit
