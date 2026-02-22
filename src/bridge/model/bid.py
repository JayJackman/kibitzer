"""Bid representations for bridge auctions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeGuard

from .card import Suit

# ── Bid types ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class PassBid:
    """A pass bid."""

    def __str__(self) -> str:
        return "Pass"

    def __repr__(self) -> str:
        return "Bid(Pass)"


@dataclass(frozen=True)
class DoubleBid:
    """A double bid."""

    def __str__(self) -> str:
        return "X"

    def __repr__(self) -> str:
        return "Bid(X)"


@dataclass(frozen=True)
class RedoubleBid:
    """A redouble bid."""

    def __str__(self) -> str:
        return "XX"

    def __repr__(self) -> str:
        return "Bid(XX)"


@dataclass(frozen=True)
class SuitBid:
    """A suit bid (including notrump) at a specific level.

    Level is 1-7, suit is any Suit (including NOTRUMP).
    """

    level: int
    suit: Suit

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 7:
            raise ValueError(f"Bid level must be 1-7, got {self.level}")

    @property
    def _sort_key(self) -> int:
        """Numeric key for ordering suit bids.

        1C=11, 1D=12, ..., 1NT=15, 2C=21, ..., 7NT=75.
        """
        return self.level * 10 + self.suit.value

    def __lt__(self, other: object) -> bool:
        """Compare suit bids for auction legality."""
        if not isinstance(other, SuitBid):
            return NotImplemented
        return self._sort_key < other._sort_key

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SuitBid):
            return NotImplemented
        return self._sort_key <= other._sort_key

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SuitBid):
            return NotImplemented
        return self._sort_key > other._sort_key

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SuitBid):
            return NotImplemented
        return self._sort_key >= other._sort_key

    def __str__(self) -> str:
        return f"{self.level}{self.suit.letter}"

    def __repr__(self) -> str:
        return f"Bid({self})"


Bid = SuitBid | PassBid | DoubleBid | RedoubleBid


# ── Singletons ─────────────────────────────────────────────────────

PASS = PassBid()
DOUBLE = DoubleBid()
REDOUBLE = RedoubleBid()


# ── Type guards ────────────────────────────────────────────────────


def is_pass(bid: Bid) -> TypeGuard[PassBid]:
    return isinstance(bid, PassBid)


def is_double(bid: Bid) -> TypeGuard[DoubleBid]:
    return isinstance(bid, DoubleBid)


def is_redouble(bid: Bid) -> TypeGuard[RedoubleBid]:
    return isinstance(bid, RedoubleBid)


def is_suit_bid(bid: Bid) -> TypeGuard[SuitBid]:
    return isinstance(bid, SuitBid)


# ── Parsing ────────────────────────────────────────────────────────

_SUIT_MAP = {
    "C": Suit.CLUBS,
    "D": Suit.DIAMONDS,
    "H": Suit.HEARTS,
    "S": Suit.SPADES,
    "NT": Suit.NOTRUMP,
    "N": Suit.NOTRUMP,
}


def parse_bid(text: str) -> Bid:
    """Parse a bid string into a Bid object.

    Accepts: 'Pass', 'P', 'X', 'XX', '1C', '1NT', '3H', '7NT', etc.
    Case-insensitive.
    """
    text = text.strip().upper()

    if text in ("PASS", "P"):
        return PASS
    if text == "XX":
        return REDOUBLE
    if text == "X":
        return DOUBLE

    if len(text) < 2 or not text[0].isdigit():
        raise ValueError(f"Invalid bid: {text!r}")

    level = int(text[0])
    suit_str = text[1:]

    if suit_str not in _SUIT_MAP:
        raise ValueError(f"Invalid suit in bid: {text!r}")

    return SuitBid(level, _SUIT_MAP[suit_str])
