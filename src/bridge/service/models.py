"""Service layer models for the bridge bidding assistant."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from bridge.engine.rule import Category, RuleResult
from bridge.model.auction import Contract, Seat
from bridge.model.bid import Bid
from bridge.model.card import Suit
from bridge.model.hand import Hand


@dataclass(frozen=True)
class Player:
    """A player at the table."""

    name: str


@unique
class TableStatus(StrEnum):
    """Current state of a table session."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class HandEvaluation:
    """Pre-computed hand metrics in a UI-friendly structure."""

    hcp: int
    length_points: int
    total_points: int
    distribution_points: int
    controls: int
    quick_tricks: float
    losers: int
    shape: tuple[int, int, int, int]
    sorted_shape: tuple[int, ...]
    is_balanced: bool
    is_semi_balanced: bool
    longest_suit: Suit


@dataclass(frozen=True)
class BiddingAdvice:
    """Complete bid recommendation from the advisor."""

    recommended: RuleResult
    alternatives: list[RuleResult]
    hand_evaluation: HandEvaluation
    phase: Category


@dataclass(frozen=True)
class TableView:
    """Filtered view of a table for a specific seat (no other hands visible)."""

    seat: Seat
    hand: Hand | None
    seats: dict[Seat, Player | None]
    bids: list[tuple[Seat, Bid]]
    current_seat: Seat
    is_complete: bool
    contract: Contract | None
    status: TableStatus


@dataclass(frozen=True)
class TableSummary:
    """Lightweight view for lobby listing."""

    id: str
    status: TableStatus
    seats: dict[Seat, Player | None]
    num_players: int


# ── Exceptions ────────────────────────────────────────────────────


class SeatOccupiedError(Exception):
    """Raised when trying to join an occupied seat."""


class SeatEmptyError(Exception):
    """Raised when operating on an empty seat."""


class NotYourTurnError(Exception):
    """Raised when bidding out of turn."""


class TableNotFoundError(Exception):
    """Raised when a table ID doesn't exist."""


class AuctionCompleteError(Exception):
    """Raised when trying to bid after auction ends."""


class HandNotSetError(Exception):
    """Raised when requesting advice without a hand."""


class UnauthorizedBidError(Exception):
    """Raised when a player tries to bid for another player's seat."""


class PlayerNotSeatedError(Exception):
    """Raised when a player not seated at the table tries to act."""


class DuplicateCardError(Exception):
    """Raised when a hand shares cards with another seat's hand.

    Message names conflicting seats only, not the cards.
    """
