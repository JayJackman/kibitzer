"""Hand representation for bridge — an immutable 13-card hand."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .card import SUITS_SHDC, Card, Rank, Suit


class _CardCollector:
    """Accumulates cards during parsing, checking for duplicates."""

    def __init__(self) -> None:
        self._cards: set[Card] = set()

    def add(self, suit: Suit, rank: Rank) -> None:
        card = Card(suit, rank)
        if card in self._cards:
            raise ValueError(f"Duplicate card: {card}")
        self._cards.add(card)

    def freeze(self) -> frozenset[Card]:
        return frozenset(self._cards)


@dataclass(frozen=True)
class Hand:
    """An immutable 13-card bridge hand."""

    cards: frozenset[Card]

    def __post_init__(self) -> None:
        if len(self.cards) != 13:
            raise ValueError(
                f"A hand must have exactly 13 cards, got {len(self.cards)}"
            )

    def suit_cards(self, suit: Suit) -> tuple[Card, ...]:
        """Cards in a suit, sorted high to low by rank."""
        return tuple(
            sorted(
                (c for c in self.cards if c.suit == suit),
                key=lambda c: c.rank,
                reverse=True,
            )
        )

    def suit_length(self, suit: Suit) -> int:
        """Number of cards in a suit."""
        return sum(1 for c in self.cards if c.suit == suit)

    @property
    def spades(self) -> tuple[Card, ...]:
        """Spade cards, sorted high to low."""
        return self.suit_cards(Suit.SPADES)

    @property
    def hearts(self) -> tuple[Card, ...]:
        """Heart cards, sorted high to low."""
        return self.suit_cards(Suit.HEARTS)

    @property
    def diamonds(self) -> tuple[Card, ...]:
        """Diamond cards, sorted high to low."""
        return self.suit_cards(Suit.DIAMONDS)

    @property
    def clubs(self) -> tuple[Card, ...]:
        """Club cards, sorted high to low."""
        return self.suit_cards(Suit.CLUBS)

    @property
    def shape(self) -> tuple[int, int, int, int]:
        """Suit lengths in S-H-D-C order."""
        return (
            self.suit_length(Suit.SPADES),
            self.suit_length(Suit.HEARTS),
            self.suit_length(Suit.DIAMONDS),
            self.suit_length(Suit.CLUBS),
        )

    @property
    def sorted_shape(self) -> tuple[int, ...]:
        """Shape sorted descending (e.g., 5-4-3-1)."""
        return tuple(sorted(self.shape, reverse=True))

    @property
    def is_balanced(self) -> bool:
        """4333, 4432, or 5332."""
        return self.sorted_shape in ((4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2))

    @property
    def is_semi_balanced(self) -> bool:
        """Balanced plus 5422, 6322."""
        return self.is_balanced or self.sorted_shape in (
            (5, 4, 2, 2),
            (6, 3, 2, 2),
        )

    @property
    def longest_suit(self) -> Suit:
        """Longest suit. Higher-ranking suit wins ties."""
        return max((self.suit_length(s), s) for s in SUITS_SHDC)[1]

    def has_card(self, suit: Suit, rank: Rank) -> bool:
        """Check if the hand contains a specific card."""
        return Card(suit, rank) in self.cards

    def __str__(self) -> str:
        """PBN-style display: S.H.D.C with cards high-to-low."""
        parts: list[str] = []
        for suit in SUITS_SHDC:
            cards = self.suit_cards(suit)
            parts.append("".join(str(c.rank) for c in cards))
        return ".".join(parts)

    @classmethod
    def from_pbn(cls, pbn: str) -> Hand:
        """Parse PBN format: 'AKJ52.KQ3.84.A73' (S.H.D.C order).

        Cards within each suit are rank characters (2-9, T, J, Q, K, A).
        """
        parts = pbn.strip().split(".")
        if len(parts) != 4:
            raise ValueError(
                f"PBN format requires exactly 4 dot-separated groups, got {len(parts)}"
            )
        collector = _CardCollector()
        for suit, part in zip(SUITS_SHDC, parts, strict=True):
            for char in part:
                collector.add(suit, Rank.from_char(char))
        return cls(collector.freeze())

    @classmethod
    def from_labeled(cls, text: str) -> Hand:
        """Parse labeled format: 'S:AKJ52 H:KQ3 D:84 C:A73'.

        Suit labels (S:/H:/D:/C:) followed by rank characters.
        """
        collector = _CardCollector()
        for match in re.finditer(r"([SHDC]):([2-9TJQKA]*)", text.upper()):
            suit = Suit.from_letter(match.group(1))
            for char in match.group(2):
                collector.add(suit, Rank.from_char(char))
        return cls(collector.freeze())

    @classmethod
    def from_compact(cls, text: str) -> Hand:
        """Parse compact format: 'SAKJ52HKQ3D84CA73'.

        Suit letter immediately followed by rank characters, no separators.
        """
        collector = _CardCollector()
        current_suit: Suit | None = None
        for char in text.upper():
            if char in "SHDC":
                current_suit = Suit.from_letter(char)
            elif current_suit is not None:
                collector.add(current_suit, Rank.from_char(char))
            else:
                raise ValueError(f"Expected suit letter (S/H/D/C), got {char!r}")
        return cls(collector.freeze())
