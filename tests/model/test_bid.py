"""Tests for Bid, BidType, and parse_bid."""

import pytest

from bridge.model.bid import Bid, BidType, parse_bid
from bridge.model.card import Suit


class TestBidCreation:
    def test_suit_bid(self) -> None:
        bid = Bid.suit_bid(1, Suit.HEARTS)
        assert bid.bid_type == BidType.SUIT
        assert bid.level == 1
        assert bid.suit == Suit.HEARTS

    def test_pass(self) -> None:
        bid = Bid.make_pass()
        assert bid.is_pass
        assert bid.level is None
        assert bid.suit is None

    def test_double(self) -> None:
        bid = Bid.double()
        assert bid.is_double

    def test_redouble(self) -> None:
        bid = Bid.redouble()
        assert bid.is_redouble

    def test_invalid_level(self) -> None:
        with pytest.raises(ValueError, match="level must be 1-7"):
            Bid.suit_bid(0, Suit.CLUBS)
        with pytest.raises(ValueError, match="level must be 1-7"):
            Bid.suit_bid(8, Suit.CLUBS)

    def test_pass_with_level_raises(self) -> None:
        with pytest.raises(ValueError, match="must not have level"):
            Bid(BidType.PASS, level=1)


class TestBidStr:
    def test_suit_bids(self) -> None:
        assert str(Bid.suit_bid(1, Suit.CLUBS)) == "1C"
        assert str(Bid.suit_bid(3, Suit.HEARTS)) == "3H"
        assert str(Bid.suit_bid(1, Suit.NOTRUMP)) == "1NT"
        assert str(Bid.suit_bid(7, Suit.NOTRUMP)) == "7NT"

    def test_special_bids(self) -> None:
        assert str(Bid.make_pass()) == "Pass"
        assert str(Bid.double()) == "X"
        assert str(Bid.redouble()) == "XX"

    def test_repr(self) -> None:
        assert repr(Bid.suit_bid(1, Suit.HEARTS)) == "Bid(1H)"
        assert repr(Bid.make_pass()) == "Bid(Pass)"


class TestBidOrdering:
    def test_suit_bids_order(self) -> None:
        one_club = Bid.suit_bid(1, Suit.CLUBS)
        one_diamond = Bid.suit_bid(1, Suit.DIAMONDS)
        one_nt = Bid.suit_bid(1, Suit.NOTRUMP)
        two_clubs = Bid.suit_bid(2, Suit.CLUBS)
        seven_nt = Bid.suit_bid(7, Suit.NOTRUMP)

        assert one_club < one_diamond
        assert one_diamond < one_nt
        assert one_nt < two_clubs
        assert two_clubs < seven_nt

    def test_non_suit_bid_ordering_raises(self) -> None:
        with pytest.raises(TypeError, match="Cannot compare"):
            _ = Bid.make_pass() < Bid.suit_bid(1, Suit.CLUBS)


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
