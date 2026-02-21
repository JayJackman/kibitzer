"""Tests for Card, Suit, and Rank."""

import pytest

from bridge.model.card import Card, Rank, Suit


class TestSuit:
    def test_ordering(self) -> None:
        assert Suit.CLUBS < Suit.DIAMONDS < Suit.HEARTS < Suit.SPADES

    def test_is_major(self) -> None:
        assert Suit.HEARTS.is_major
        assert Suit.SPADES.is_major
        assert not Suit.CLUBS.is_major
        assert not Suit.DIAMONDS.is_major

    def test_is_minor(self) -> None:
        assert Suit.CLUBS.is_minor
        assert Suit.DIAMONDS.is_minor
        assert not Suit.HEARTS.is_minor
        assert not Suit.SPADES.is_minor

    def test_str_is_symbol(self) -> None:
        assert str(Suit.CLUBS) == "♣"
        assert str(Suit.DIAMONDS) == "♦"
        assert str(Suit.HEARTS) == "♥"
        assert str(Suit.SPADES) == "♠"

    def test_letter(self) -> None:
        assert Suit.CLUBS.letter == "C"
        assert Suit.DIAMONDS.letter == "D"
        assert Suit.HEARTS.letter == "H"
        assert Suit.SPADES.letter == "S"

    def test_from_letter(self) -> None:
        assert Suit.from_letter("C") == Suit.CLUBS
        assert Suit.from_letter("d") == Suit.DIAMONDS
        assert Suit.from_letter("H") == Suit.HEARTS
        assert Suit.from_letter("s") == Suit.SPADES

    def test_from_letter_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid suit letter"):
            Suit.from_letter("X")


class TestRank:
    def test_ordering(self) -> None:
        assert Rank.TWO < Rank.THREE < Rank.ACE

    def test_hcp(self) -> None:
        assert Rank.TWO.hcp == 0
        assert Rank.NINE.hcp == 0
        assert Rank.TEN.hcp == 0
        assert Rank.JACK.hcp == 1
        assert Rank.QUEEN.hcp == 2
        assert Rank.KING.hcp == 3
        assert Rank.ACE.hcp == 4

    def test_str(self) -> None:
        assert str(Rank.TWO) == "2"
        assert str(Rank.NINE) == "9"
        assert str(Rank.TEN) == "T"
        assert str(Rank.JACK) == "J"
        assert str(Rank.QUEEN) == "Q"
        assert str(Rank.KING) == "K"
        assert str(Rank.ACE) == "A"

    def test_from_char(self) -> None:
        assert Rank.from_char("2") == Rank.TWO
        assert Rank.from_char("T") == Rank.TEN
        assert Rank.from_char("t") == Rank.TEN
        assert Rank.from_char("A") == Rank.ACE
        assert Rank.from_char("a") == Rank.ACE

    def test_from_char_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid rank character"):
            Rank.from_char("X")
        with pytest.raises(ValueError, match="Invalid rank character"):
            Rank.from_char("1")


class TestCard:
    def test_creation(self) -> None:
        card = Card(Suit.SPADES, Rank.ACE)
        assert card.suit == Suit.SPADES
        assert card.rank == Rank.ACE

    def test_str(self) -> None:
        assert str(Card(Suit.SPADES, Rank.ACE)) == "A♠"
        assert str(Card(Suit.HEARTS, Rank.KING)) == "K♥"
        assert str(Card(Suit.CLUBS, Rank.TWO)) == "2♣"

    def test_repr(self) -> None:
        assert repr(Card(Suit.SPADES, Rank.ACE)) == "Card(SA)"

    def test_ordering(self) -> None:
        # Same suit, different rank
        two_clubs = Card(Suit.CLUBS, Rank.TWO)
        ace_clubs = Card(Suit.CLUBS, Rank.ACE)
        assert two_clubs < ace_clubs

        # Different suit
        ace_clubs = Card(Suit.CLUBS, Rank.ACE)
        two_spades = Card(Suit.SPADES, Rank.TWO)
        assert ace_clubs < two_spades

    def test_frozen(self) -> None:
        card = Card(Suit.SPADES, Rank.ACE)
        with pytest.raises(AttributeError):
            card.suit = Suit.HEARTS  # type: ignore[misc]

    def test_equality(self) -> None:
        c1 = Card(Suit.SPADES, Rank.ACE)
        c2 = Card(Suit.SPADES, Rank.ACE)
        assert c1 == c2
        assert c1 is not c2

    def test_hashable(self) -> None:
        c1 = Card(Suit.SPADES, Rank.ACE)
        c2 = Card(Suit.SPADES, Rank.ACE)
        assert hash(c1) == hash(c2)
        assert len({c1, c2}) == 1
