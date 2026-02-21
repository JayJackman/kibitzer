"""Bid representations for bridge auctions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto, unique

from .card import Suit


@unique
class BidType(IntEnum):
    """The type of bid action."""

    PASS = auto()
    SUIT = auto()
    DOUBLE = auto()
    REDOUBLE = auto()


@dataclass(frozen=True)
class Bid:
    """A single bid in the auction.

    For suit bids, level (1-7) and suit are required.
    For Pass/Double/Redouble, level and suit must be None.
    """

    bid_type: BidType
    level: int | None = None
    suit: Suit | None = None

    def __post_init__(self) -> None:
        if self.bid_type == BidType.SUIT:
            if self.level is None or self.suit is None:
                raise ValueError("Suit bids require level and suit")
            if not 1 <= self.level <= 7:
                raise ValueError(f"Bid level must be 1-7, got {self.level}")
        else:
            if self.level is not None or self.suit is not None:
                raise ValueError(
                    f"{self.bid_type.name} bids must not have level or suit"
                )

    @property
    def is_pass(self) -> bool:
        return self.bid_type == BidType.PASS

    @property
    def is_double(self) -> bool:
        return self.bid_type == BidType.DOUBLE

    @property
    def is_redouble(self) -> bool:
        return self.bid_type == BidType.REDOUBLE

    @property
    def _sort_key(self) -> int:
        """Numeric key for ordering suit bids.

        1C=11, 1D=12, ..., 1NT=15, 2C=21, ..., 7NT=75.
        Non-suit bids are not orderable against suit bids.
        """
        if self.bid_type != BidType.SUIT:
            raise TypeError(f"Cannot compare {self.bid_type.name} with suit bids")
        assert self.level is not None and self.suit is not None
        return self.level * 10 + self.suit.value

    def __lt__(self, other: object) -> bool:
        """Compare suit bids for auction legality."""
        if not isinstance(other, Bid):
            return NotImplemented
        return self._sort_key < other._sort_key

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Bid):
            return NotImplemented
        return self._sort_key <= other._sort_key

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Bid):
            return NotImplemented
        return self._sort_key > other._sort_key

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Bid):
            return NotImplemented
        return self._sort_key >= other._sort_key

    def __str__(self) -> str:
        if self.bid_type == BidType.PASS:
            return "Pass"
        if self.bid_type == BidType.DOUBLE:
            return "X"
        if self.bid_type == BidType.REDOUBLE:
            return "XX"
        assert self.level is not None and self.suit is not None
        return f"{self.level}{self.suit.letter}"

    def __repr__(self) -> str:
        return f"Bid({self})"

    # --- Factory methods ---

    @classmethod
    def make_pass(cls) -> Bid:
        return cls(BidType.PASS)

    @classmethod
    def double(cls) -> Bid:
        return cls(BidType.DOUBLE)

    @classmethod
    def redouble(cls) -> Bid:
        return cls(BidType.REDOUBLE)

    @classmethod
    def suit_bid(cls, level: int, suit: Suit) -> Bid:
        return cls(BidType.SUIT, level, suit)


# --- Parsing ---

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
        return Bid.make_pass()
    if text == "XX":
        return Bid.redouble()
    if text == "X":
        return Bid.double()

    if len(text) < 2 or not text[0].isdigit():
        raise ValueError(f"Invalid bid: {text!r}")

    level = int(text[0])
    suit_str = text[1:]

    if suit_str not in _SUIT_MAP:
        raise ValueError(f"Invalid suit in bid: {text!r}")

    return Bid.suit_bid(level, _SUIT_MAP[suit_str])
