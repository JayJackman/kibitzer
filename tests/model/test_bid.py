"""Tests for Bid, Strain, BidType, and parse_bid."""

import pytest

from bridge.model.bid import Bid, BidType, Strain, parse_bid


class TestStrain:
    def test_ordering(self) -> None:
        assert Strain.CLUBS < Strain.DIAMONDS < Strain.HEARTS
        assert Strain.HEARTS < Strain.SPADES < Strain.NOTRUMP

    def test_is_major(self) -> None:
        assert Strain.HEARTS.is_major
        assert Strain.SPADES.is_major
        assert not Strain.CLUBS.is_major
        assert not Strain.NOTRUMP.is_major

    def test_is_minor(self) -> None:
        assert Strain.CLUBS.is_minor
        assert Strain.DIAMONDS.is_minor
        assert not Strain.HEARTS.is_minor
        assert not Strain.NOTRUMP.is_minor

    def test_from_suit(self) -> None:
        from bridge.model.card import Suit

        assert Strain.from_suit(Suit.SPADES) == Strain.SPADES
        assert Strain.from_suit(Suit.CLUBS) == Strain.CLUBS

    def test_str(self) -> None:
        assert str(Strain.NOTRUMP) == "NT"
        assert str(Strain.SPADES) == "♠"

    def test_letter(self) -> None:
        assert Strain.NOTRUMP.letter == "NT"
        assert Strain.SPADES.letter == "S"


class TestBidCreation:
    def test_suit_bid(self) -> None:
        bid = Bid.suit_bid(1, Strain.HEARTS)
        assert bid.bid_type == BidType.SUIT
        assert bid.level == 1
        assert bid.strain == Strain.HEARTS

    def test_pass(self) -> None:
        bid = Bid.make_pass()
        assert bid.is_pass
        assert bid.level is None
        assert bid.strain is None

    def test_double(self) -> None:
        bid = Bid.double()
        assert bid.is_double

    def test_redouble(self) -> None:
        bid = Bid.redouble()
        assert bid.is_redouble

    def test_invalid_level(self) -> None:
        with pytest.raises(ValueError, match="level must be 1-7"):
            Bid.suit_bid(0, Strain.CLUBS)
        with pytest.raises(ValueError, match="level must be 1-7"):
            Bid.suit_bid(8, Strain.CLUBS)

    def test_pass_with_level_raises(self) -> None:
        with pytest.raises(ValueError, match="must not have level"):
            Bid(BidType.PASS, level=1)


class TestBidStr:
    def test_suit_bids(self) -> None:
        assert str(Bid.suit_bid(1, Strain.CLUBS)) == "1C"
        assert str(Bid.suit_bid(3, Strain.HEARTS)) == "3H"
        assert str(Bid.suit_bid(1, Strain.NOTRUMP)) == "1NT"
        assert str(Bid.suit_bid(7, Strain.NOTRUMP)) == "7NT"

    def test_special_bids(self) -> None:
        assert str(Bid.make_pass()) == "Pass"
        assert str(Bid.double()) == "X"
        assert str(Bid.redouble()) == "XX"

    def test_repr(self) -> None:
        assert repr(Bid.suit_bid(1, Strain.HEARTS)) == "Bid(1H)"
        assert repr(Bid.make_pass()) == "Bid(Pass)"


class TestBidOrdering:
    def test_suit_bids_order(self) -> None:
        one_club = Bid.suit_bid(1, Strain.CLUBS)
        one_diamond = Bid.suit_bid(1, Strain.DIAMONDS)
        one_nt = Bid.suit_bid(1, Strain.NOTRUMP)
        two_clubs = Bid.suit_bid(2, Strain.CLUBS)
        seven_nt = Bid.suit_bid(7, Strain.NOTRUMP)

        assert one_club < one_diamond
        assert one_diamond < one_nt
        assert one_nt < two_clubs
        assert two_clubs < seven_nt

    def test_non_suit_bid_ordering_raises(self) -> None:
        with pytest.raises(TypeError, match="Cannot compare"):
            _ = Bid.make_pass() < Bid.suit_bid(1, Strain.CLUBS)


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

    def test_invalid_strain(self) -> None:
        with pytest.raises(ValueError, match="Invalid strain"):
            parse_bid("1X")
