"""Tests for bid types, singletons, type guards, and parse_bid."""

import pytest

from bridge.model.bid import (
    DOUBLE,
    PASS,
    REDOUBLE,
    DoubleBid,
    PassBid,
    RedoubleBid,
    SuitBid,
    is_double,
    is_pass,
    is_redouble,
    is_suit_bid,
    parse_bid,
)
from bridge.model.card import Suit


class TestSuitBid:
    def test_creation(self) -> None:
        bid = SuitBid(1, Suit.HEARTS)
        assert bid.level == 1
        assert bid.suit == Suit.HEARTS

    def test_invalid_level(self) -> None:
        with pytest.raises(ValueError, match="level must be 1-7"):
            SuitBid(0, Suit.CLUBS)
        with pytest.raises(ValueError, match="level must be 1-7"):
            SuitBid(8, Suit.CLUBS)

    def test_str(self) -> None:
        assert str(SuitBid(1, Suit.CLUBS)) == "1C"
        assert str(SuitBid(3, Suit.HEARTS)) == "3H"
        assert str(SuitBid(1, Suit.NOTRUMP)) == "1NT"
        assert str(SuitBid(7, Suit.NOTRUMP)) == "7NT"

    def test_repr(self) -> None:
        assert repr(SuitBid(1, Suit.HEARTS)) == "Bid(1H)"


class TestSingletons:
    def test_pass(self) -> None:
        assert str(PASS) == "Pass"
        assert repr(PASS) == "Bid(Pass)"

    def test_double(self) -> None:
        assert str(DOUBLE) == "X"
        assert repr(DOUBLE) == "Bid(X)"

    def test_redouble(self) -> None:
        assert str(REDOUBLE) == "XX"
        assert repr(REDOUBLE) == "Bid(XX)"

    def test_singleton_identity(self) -> None:
        assert PassBid() == PASS
        assert DoubleBid() == DOUBLE
        assert RedoubleBid() == REDOUBLE


class TestTypeGuards:
    def test_is_pass(self) -> None:
        assert is_pass(PASS)
        assert not is_pass(DOUBLE)
        assert not is_pass(SuitBid(1, Suit.CLUBS))

    def test_is_double(self) -> None:
        assert is_double(DOUBLE)
        assert not is_double(PASS)

    def test_is_redouble(self) -> None:
        assert is_redouble(REDOUBLE)
        assert not is_redouble(PASS)

    def test_is_suit_bid(self) -> None:
        assert is_suit_bid(SuitBid(1, Suit.HEARTS))
        assert not is_suit_bid(PASS)
        assert not is_suit_bid(DOUBLE)


class TestBidOrdering:
    def test_suit_bids_order(self) -> None:
        one_club = SuitBid(1, Suit.CLUBS)
        one_diamond = SuitBid(1, Suit.DIAMONDS)
        one_nt = SuitBid(1, Suit.NOTRUMP)
        two_clubs = SuitBid(2, Suit.CLUBS)
        seven_nt = SuitBid(7, Suit.NOTRUMP)

        assert one_club < one_diamond
        assert one_diamond < one_nt
        assert one_nt < two_clubs
        assert two_clubs < seven_nt

    def test_non_suit_bid_ordering_raises(self) -> None:
        with pytest.raises(TypeError):
            _ = SuitBid(1, Suit.CLUBS) > PASS  # type: ignore[operator]


class TestParseBid:
    @pytest.mark.parametrize(
        ("text", "expected_str"),
        [
            ("1C", "1C"),
            ("1c", "1C"),
            ("1NT", "1NT"),
            ("1nt", "1NT"),
            ("1N", "1NT"),
            ("3H", "3H"),
            ("7NT", "7NT"),
            ("Pass", "Pass"),
            ("pass", "Pass"),
            ("P", "Pass"),
            ("p", "Pass"),
            ("X", "X"),
            ("x", "X"),
            ("XX", "XX"),
            ("xx", "XX"),
        ],
    )
    def test_valid_bids(self, text: str, expected_str: str) -> None:
        bid = parse_bid(text)
        assert str(bid) == expected_str

    def test_invalid_bid(self) -> None:
        with pytest.raises(ValueError, match="Invalid bid"):
            parse_bid("ZZ")

    def test_invalid_suit(self) -> None:
        with pytest.raises(ValueError, match="Invalid suit"):
            parse_bid("1X")
