"""Board container — bundles hand, seat, and auction for a bidding decision."""

from dataclasses import dataclass

from .auction import AuctionState, Seat
from .hand import Hand


@dataclass(frozen=True)
class Board:
    """A complete board context for a bidding decision.

    Combines the player's hand, their seat position, and the current
    auction state (which includes vulnerability and dealer).
    """

    hand: Hand
    seat: Seat
    auction: AuctionState
