"""Tests for Hand."""

import pytest

from bridge.model.card import Rank, Suit
from bridge.model.hand import Hand

# A well-known hand: S:AKJ52 H:KQ3 D:84 C:A73
SAMPLE_PBN = "AKJ52.KQ3.84.A73"


class TestHandCreation:
    def test_from_pbn(self) -> None:
        hand = Hand.from_pbn(SAMPLE_PBN)
        assert len(hand.cards) == 13
        assert hand.has_card(Suit.SPADES, Rank.ACE)
        assert hand.has_card(Suit.SPADES, Rank.KING)
        assert hand.has_card(Suit.HEARTS, Rank.QUEEN)
        assert hand.has_card(Suit.CLUBS, Rank.ACE)

    def test_from_labeled(self) -> None:
        hand = Hand.from_labeled("S:AKJ52 H:KQ3 D:84 C:A73")
        assert hand == Hand.from_pbn(SAMPLE_PBN)

    def test_from_compact(self) -> None:
        hand = Hand.from_compact("SAKJ52HKQ3D84CA73")
        assert hand == Hand.from_pbn(SAMPLE_PBN)

    def test_all_formats_equivalent(self) -> None:
        pbn = Hand.from_pbn(SAMPLE_PBN)
        labeled = Hand.from_labeled("S:AKJ52 H:KQ3 D:84 C:A73")
        compact = Hand.from_compact("SAKJ52HKQ3D84CA73")
        assert pbn == labeled == compact

    def test_wrong_card_count(self) -> None:
        with pytest.raises(ValueError, match="exactly 13 cards"):
            Hand.from_pbn("AKJ52.KQ3.84.A7")  # only 12

    def test_duplicate_cards(self) -> None:
        with pytest.raises(ValueError, match="Duplicate card"):
            Hand.from_pbn("AAKJ5.KQ3.842.A73")  # two aces of spades

    def test_pbn_wrong_groups(self) -> None:
        with pytest.raises(ValueError, match="4 dot-separated"):
            Hand.from_pbn("AKJ52.KQ3.84")  # only 3 groups

    def test_void_suit(self) -> None:
        # Void in diamonds: S:AKQJ52 H:KQ32 D:- C:A7
        hand = Hand.from_pbn("AKQJ52.KQ32..A73")
        assert hand.suit_length(Suit.DIAMONDS) == 0
        assert hand.suit_length(Suit.SPADES) == 6

    def test_compact_no_suit_prefix(self) -> None:
        with pytest.raises(ValueError, match="Expected suit letter"):
            Hand.from_compact("AKJ52HKQ3D84CA73")  # missing S prefix


class TestHandQueries:
    @pytest.fixture()
    def hand(self) -> Hand:
        return Hand.from_pbn(SAMPLE_PBN)

    def test_suit_cards(self, hand: Hand) -> None:
        spades = hand.suit_cards(Suit.SPADES)
        assert len(spades) == 5
        # Sorted high to low
        ranks = [c.rank for c in spades]
        assert ranks == [Rank.ACE, Rank.KING, Rank.JACK, Rank.FIVE, Rank.TWO]

    def test_suit_length(self, hand: Hand) -> None:
        assert hand.suit_length(Suit.SPADES) == 5
        assert hand.suit_length(Suit.HEARTS) == 3
        assert hand.suit_length(Suit.DIAMONDS) == 2
        assert hand.suit_length(Suit.CLUBS) == 3

    def test_shape(self, hand: Hand) -> None:
        assert hand.shape == (5, 3, 2, 3)  # S, H, D, C

    def test_sorted_shape(self, hand: Hand) -> None:
        assert hand.sorted_shape == (5, 3, 3, 2)

    def test_has_card(self, hand: Hand) -> None:
        assert hand.has_card(Suit.SPADES, Rank.ACE)
        assert not hand.has_card(Suit.SPADES, Rank.QUEEN)

    def test_longest_suit(self, hand: Hand) -> None:
        assert hand.longest_suit == Suit.SPADES


class TestHandBalance:
    def test_balanced_4333(self) -> None:
        hand = Hand.from_pbn("AK32.KQ3.J84.Q73")
        assert hand.is_balanced
        assert hand.is_semi_balanced

    def test_balanced_4432(self) -> None:
        hand = Hand.from_pbn("AK32.KQ32.J8.Q73")
        assert hand.is_balanced
        assert hand.is_semi_balanced

    def test_balanced_5332(self) -> None:
        hand = Hand.from_pbn("AKJ52.KQ3.84.A73")
        assert hand.is_balanced
        assert hand.is_semi_balanced

    def test_semi_balanced_5422(self) -> None:
        hand = Hand.from_pbn("AKJ52.KQ32.84.A7")
        assert not hand.is_balanced
        assert hand.is_semi_balanced

    def test_semi_balanced_6322(self) -> None:
        hand = Hand.from_pbn("AKJ532.KQ3.84.A7")
        assert not hand.is_balanced
        assert hand.is_semi_balanced

    def test_unbalanced(self) -> None:
        # 6-4-2-1
        hand = Hand.from_pbn("AKJ532.KQ32.8.A7")
        assert not hand.is_balanced
        assert not hand.is_semi_balanced


class TestHandStr:
    def test_str_roundtrip(self) -> None:
        hand = Hand.from_pbn(SAMPLE_PBN)
        assert str(hand) == SAMPLE_PBN

    def test_str_void(self) -> None:
        hand = Hand.from_pbn("AKQJ52.KQ32..A73")
        assert str(hand) == "AKQJ52.KQ32..A73"


class TestHandEquality:
    def test_equal_hands(self) -> None:
        h1 = Hand.from_pbn(SAMPLE_PBN)
        h2 = Hand.from_pbn(SAMPLE_PBN)
        assert h1 == h2

    def test_frozen(self) -> None:
        hand = Hand.from_pbn(SAMPLE_PBN)
        with pytest.raises(AttributeError):
            hand.cards = frozenset()  # type: ignore[misc]

    def test_hashable(self) -> None:
        h1 = Hand.from_pbn(SAMPLE_PBN)
        h2 = Hand.from_pbn(SAMPLE_PBN)
        assert hash(h1) == hash(h2)
        assert len({h1, h2}) == 1
