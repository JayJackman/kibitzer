"""Bid representations for bridge auctions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto, unique

from .card import Suit


@unique
class Strain(IntEnum):
    """Strain for bids, including notrump."""

    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4
    NOTRUMP = 5

    @property
    def is_major(self) -> bool:
        return self in (Strain.HEARTS, Strain.SPADES)

    @property
    def is_minor(self) -> bool:
        return self in (Strain.CLUBS, Strain.DIAMONDS)

    @classmethod
    def from_suit(cls, suit: Suit) -> Strain:
        """Convert a card Suit to a bid Strain."""
        return cls(suit.value)

    def __str__(self) -> str:
        if self == Strain.NOTRUMP:
            return "NT"
        return {
            Strain.CLUBS: "♣",
            Strain.DIAMONDS: "♦",
            Strain.HEARTS: "♥",
            Strain.SPADES: "♠",
        }[self]

    @property
    def letter(self) -> str:
        """Short letter code for parsing: C, D, H, S, NT."""
        return {
            Strain.CLUBS: "C",
            Strain.DIAMONDS: "D",
            Strain.HEARTS: "H",
            Strain.SPADES: "S",
            Strain.NOTRUMP: "NT",
        }[self]


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

    For suit bids, level (1-7) and strain are required.
    For Pass/Double/Redouble, level and strain must be None.
    """

    bid_type: BidType
    level: int | None = None
    strain: Strain | None = None

    def __post_init__(self) -> None:
        if self.bid_type == BidType.SUIT:
            if self.level is None or self.strain is None:
                raise ValueError("Suit bids require level and strain")
            if not 1 <= self.level <= 7:
                raise ValueError(f"Bid level must be 1-7, got {self.level}")
        else:
            if self.level is not None or self.strain is not None:
                raise ValueError(
                    f"{self.bid_type.name} bids must not have level or strain"
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
        assert self.level is not None and self.strain is not None
        return self.level * 10 + self.strain.value

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
        assert self.level is not None and self.strain is not None
        return f"{self.level}{self.strain.letter}"

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
    def suit_bid(cls, level: int, strain: Strain) -> Bid:
        return cls(BidType.SUIT, level, strain)


# --- Parsing ---

_STRAIN_MAP = {
    "C": Strain.CLUBS,
    "D": Strain.DIAMONDS,
    "H": Strain.HEARTS,
    "S": Strain.SPADES,
    "NT": Strain.NOTRUMP,
    "N": Strain.NOTRUMP,
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
    strain_str = text[1:]

    if strain_str not in _STRAIN_MAP:
        raise ValueError(f"Invalid strain in bid: {text!r}")

    return Bid.suit_bid(level, _STRAIN_MAP[strain_str])
