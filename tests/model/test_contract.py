"""Tests for Contract derivation on AuctionState."""

from bridge.model.auction import NS_VULNERABLE, AuctionState, Seat
from bridge.model.bid import DOUBLE, PASS, REDOUBLE, SuitBid
from bridge.model.card import Suit


class TestContractPassedOut:
    def test_four_passes(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        for _ in range(4):
            auction.add_bid(PASS)
        contract = auction.contract
        assert contract is not None
        assert contract.passed_out

    def test_incomplete_auction_returns_none(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))
        assert auction.contract is None

    def test_empty_auction_returns_none(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        assert auction.contract is None


class TestContractDeclarer:
    def test_simple_contract(self) -> None:
        """N opens 1H, three passes -> N declares 1H."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))
        for _ in range(3):
            auction.add_bid(PASS)
        contract = auction.contract
        assert contract is not None
        assert not contract.passed_out
        assert contract.level == 1
        assert contract.suit == Suit.HEARTS
        assert contract.declarer == Seat.NORTH
        assert not contract.doubled
        assert not contract.redoubled

    def test_declarer_is_first_to_bid_suit(self) -> None:
        """N opens 1H, S raises to 2H, three passes -> N declares (first to bid H)."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N
        auction.add_bid(PASS)  # E
        auction.add_bid(SuitBid(2, Suit.HEARTS))  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(PASS)  # N
        auction.add_bid(PASS)  # E
        contract = auction.contract
        assert contract is not None
        assert contract.level == 2
        assert contract.suit == Suit.HEARTS
        assert contract.declarer == Seat.NORTH

    def test_declarer_partner_bid_suit_first(self) -> None:
        """N opens 1D, S bids 1H, N raises to 2H -> S declares (first to bid H)."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.DIAMONDS))  # N
        auction.add_bid(PASS)  # E
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(SuitBid(2, Suit.HEARTS))  # N
        auction.add_bid(PASS)  # E
        auction.add_bid(PASS)  # S
        auction.add_bid(PASS)  # W
        contract = auction.contract
        assert contract is not None
        assert contract.level == 2
        assert contract.suit == Suit.HEARTS
        assert contract.declarer == Seat.SOUTH

    def test_notrump_contract(self) -> None:
        """N opens 1NT, S raises to 3NT -> N declares."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.NOTRUMP))  # N
        auction.add_bid(PASS)  # E
        auction.add_bid(SuitBid(3, Suit.NOTRUMP))  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(PASS)  # N
        auction.add_bid(PASS)  # E
        contract = auction.contract
        assert contract is not None
        assert contract.level == 3
        assert contract.suit == Suit.NOTRUMP
        assert contract.declarer == Seat.NORTH

    def test_different_dealer(self) -> None:
        """East deals and opens 1S -> E declares."""
        auction = AuctionState(dealer=Seat.EAST)
        auction.add_bid(SuitBid(1, Suit.SPADES))  # E
        for _ in range(3):
            auction.add_bid(PASS)
        contract = auction.contract
        assert contract is not None
        assert contract.declarer == Seat.EAST
        assert contract.suit == Suit.SPADES


class TestContractDoubled:
    def test_doubled_contract(self) -> None:
        """N opens 1H, E doubles, three passes -> doubled."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N
        auction.add_bid(DOUBLE)  # E
        auction.add_bid(PASS)  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(PASS)  # N
        contract = auction.contract
        assert contract is not None
        assert contract.doubled
        assert not contract.redoubled
        assert contract.level == 1
        assert contract.suit == Suit.HEARTS
        assert contract.declarer == Seat.NORTH

    def test_redoubled_contract(self) -> None:
        """N opens 1H, E doubles, S redoubles, three passes -> redoubled."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N
        auction.add_bid(DOUBLE)  # E
        auction.add_bid(REDOUBLE)  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(PASS)  # N
        auction.add_bid(PASS)  # E
        contract = auction.contract
        assert contract is not None
        assert not contract.doubled
        assert contract.redoubled

    def test_new_bid_cancels_double(self) -> None:
        """N: 1H, E: X, S: 2H, three passes -> not doubled."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # N
        auction.add_bid(DOUBLE)  # E
        auction.add_bid(SuitBid(2, Suit.HEARTS))  # S
        auction.add_bid(PASS)  # W
        auction.add_bid(PASS)  # N
        auction.add_bid(PASS)  # E
        contract = auction.contract
        assert contract is not None
        assert not contract.doubled
        assert not contract.redoubled


class TestContractWithVulnerability:
    def test_vulnerability_preserved(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH, vulnerability=NS_VULNERABLE)
        auction.add_bid(SuitBid(1, Suit.HEARTS))
        for _ in range(3):
            auction.add_bid(PASS)
        assert auction.contract is not None
        assert auction.vulnerability == NS_VULNERABLE
