"""Tests for the random deal generator."""

import random

from bridge.model.auction import Seat
from bridge.model.card import SUITS_SHDC, Card, Rank
from bridge.service.deal import deal


class TestDeal:
    def test_four_hands_of_thirteen(self) -> None:
        hands = deal(rng=random.Random(42))
        assert len(hands) == 4
        for hand in hands.values():
            assert len(hand.cards) == 13

    def test_all_52_cards_present(self) -> None:
        hands = deal(rng=random.Random(42))
        all_cards = set()
        for hand in hands.values():
            all_cards.update(hand.cards)
        assert len(all_cards) == 52

    def test_no_duplicates_across_hands(self) -> None:
        hands = deal(rng=random.Random(42))
        all_cards: list[Card] = []
        for hand in hands.values():
            all_cards.extend(hand.cards)
        assert len(all_cards) == 52
        assert len(set(all_cards)) == 52

    def test_deterministic_with_seed(self) -> None:
        deal1 = deal(rng=random.Random(42))
        deal2 = deal(rng=random.Random(42))
        for seat in Seat:
            assert deal1[seat].cards == deal2[seat].cards

    def test_different_seeds_different_deals(self) -> None:
        deal1 = deal(rng=random.Random(42))
        deal2 = deal(rng=random.Random(99))
        # At least one seat should differ
        assert any(deal1[seat].cards != deal2[seat].cards for seat in Seat)

    def test_all_seats_present(self) -> None:
        hands = deal(rng=random.Random(42))
        for seat in [Seat.NORTH, Seat.EAST, Seat.SOUTH, Seat.WEST]:
            assert seat in hands

    def test_deck_contains_all_standard_cards(self) -> None:
        hands = deal(rng=random.Random(42))
        all_cards = set()
        for hand in hands.values():
            all_cards.update(hand.cards)
        expected = {Card(suit, rank) for suit in SUITS_SHDC for rank in Rank}
        assert all_cards == expected

    def test_no_rng_works(self) -> None:
        """Deal without explicit RNG should still produce valid hands."""
        hands = deal()
        assert len(hands) == 4
        all_cards = set()
        for hand in hands.values():
            assert len(hand.cards) == 13
            all_cards.update(hand.cards)
        assert len(all_cards) == 52
