"""Card, Suit, and Rank representations for bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, unique
from functools import total_ordering

_SUIT_SYMBOLS = {1: "♣", 2: "♦", 3: "♥", 4: "♠", 5: "NT"}
_SUIT_LETTERS = {1: "C", 2: "D", 3: "H", 4: "S", 5: "NT"}
_RANK_CHARS = {10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


@unique
class Suit(IntEnum):
    """Suits ordered by rank for bidding purposes, plus NOTRUMP for bids."""

    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4
    NOTRUMP = 5

    @property
    def is_major(self) -> bool:
        return self in (Suit.HEARTS, Suit.SPADES)

    @property
    def is_minor(self) -> bool:
        return self in (Suit.CLUBS, Suit.DIAMONDS)

    @property
    def letter(self) -> str:
        """Short abbreviation for parsing: C, D, H, S, NT."""
        return _SUIT_LETTERS[self.value]

    def __str__(self) -> str:
        return _SUIT_SYMBOLS[self.value]

    @classmethod
    def from_letter(cls, letter: str) -> Suit:
        """Parse a single letter (C/D/H/S) into a Suit."""
        letter = letter.upper()
        for suit in cls:
            if suit.letter == letter:
                return suit
        raise ValueError(f"Invalid suit letter: {letter!r}")


# Standard display order: Spades, Hearts, Diamonds, Clubs (high to low).
SUITS_SHDC = (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS)


@unique
class Rank(IntEnum):
    """Card ranks, ordered by value."""

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def hcp(self) -> int:
        """Standard 4-3-2-1 high card point value."""
        return max(0, self.value - 10)

    def __str__(self) -> str:
        if self.value <= 9:
            return str(self.value)
        return _RANK_CHARS[self.value]

    @classmethod
    def from_char(cls, char: str) -> Rank:
        """Parse a single character (2-9, T, J, Q, K, A) into a Rank."""
        char = char.upper()
        if char.isdigit() and 2 <= int(char) <= 9:
            return cls(int(char))
        reverse = {v: k for k, v in _RANK_CHARS.items()}
        if char in reverse:
            return cls(reverse[char])
        raise ValueError(f"Invalid rank character: {char!r}")


@total_ordering
@dataclass(frozen=True)
class Card:
    """A single playing card."""

    suit: Suit
    rank: Rank

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.suit, self.rank) < (other.suit, other.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card({self.suit.letter}{self.rank})"
