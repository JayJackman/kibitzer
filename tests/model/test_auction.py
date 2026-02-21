"""Tests for Seat, Vulnerability, and AuctionState."""

import pytest

from bridge.model.auction import (
    AuctionState,
    IllegalBidError,
    Seat,
    Vulnerability,
)
from bridge.model.bid import Bid, Strain, parse_bid


class TestSeat:
    def test_partner(self) -> None:
        assert Seat.NORTH.partner == Seat.SOUTH
        assert Seat.SOUTH.partner == Seat.NORTH
        assert Seat.EAST.partner == Seat.WEST
        assert Seat.WEST.partner == Seat.EAST

    def test_lho(self) -> None:
        assert Seat.NORTH.lho == Seat.EAST
        assert Seat.EAST.lho == Seat.SOUTH
        assert Seat.SOUTH.lho == Seat.WEST
        assert Seat.WEST.lho == Seat.NORTH

    def test_rho(self) -> None:
        assert Seat.NORTH.rho == Seat.WEST
        assert Seat.WEST.rho == Seat.SOUTH
        assert Seat.SOUTH.rho == Seat.EAST
        assert Seat.EAST.rho == Seat.NORTH

    def test_str(self) -> None:
        assert str(Seat.NORTH) == "N"
        assert str(Seat.EAST) == "E"

    def test_from_str(self) -> None:
        assert Seat.from_str("N") == Seat.NORTH
        assert Seat.from_str("north") == Seat.NORTH
        assert Seat.from_str("South") == Seat.SOUTH
        assert Seat.from_str("e") == Seat.EAST

    def test_from_str_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid seat"):
            Seat.from_str("X")


class TestVulnerability:
    def test_none(self) -> None:
        vul = Vulnerability()
        assert not vul.is_vulnerable(Seat.NORTH)
        assert not vul.is_vulnerable(Seat.EAST)
        assert str(vul) == "None"

    def test_ns(self) -> None:
        vul = Vulnerability(ns_vulnerable=True)
        assert vul.is_vulnerable(Seat.NORTH)
        assert vul.is_vulnerable(Seat.SOUTH)
        assert not vul.is_vulnerable(Seat.EAST)
        assert str(vul) == "NS"

    def test_ew(self) -> None:
        vul = Vulnerability(ew_vulnerable=True)
        assert not vul.is_vulnerable(Seat.NORTH)
        assert vul.is_vulnerable(Seat.EAST)
        assert str(vul) == "EW"

    def test_both(self) -> None:
        vul = Vulnerability(ns_vulnerable=True, ew_vulnerable=True)
        assert vul.is_vulnerable(Seat.NORTH)
        assert vul.is_vulnerable(Seat.EAST)
        assert str(vul) == "Both"

    def test_from_str(self) -> None:
        assert Vulnerability.from_str("None") == Vulnerability()
        assert Vulnerability.from_str("NS") == Vulnerability(ns_vulnerable=True)
        assert Vulnerability.from_str("EW") == Vulnerability(ew_vulnerable=True)
        assert Vulnerability.from_str("Both") == Vulnerability(
            ns_vulnerable=True, ew_vulnerable=True
        )
        assert Vulnerability.from_str("All") == Vulnerability(
            ns_vulnerable=True, ew_vulnerable=True
        )

    def test_from_str_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid vulnerability"):
            Vulnerability.from_str("XYZ")


class TestAuctionState:
    def test_initial_state(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        assert auction.current_seat == Seat.NORTH
        assert not auction.has_opened
        assert not auction.is_complete
        assert auction.opening_bid is None
        assert auction.last_contract_bid is None

    def test_current_seat_advances(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.make_pass())
        assert auction.current_seat == Seat.EAST
        auction.add_bid(Bid.make_pass())
        assert auction.current_seat == Seat.SOUTH

    def test_opening_bid(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.make_pass())
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        opening = auction.opening_bid
        assert opening is not None
        assert opening[0] == Seat.EAST
        assert str(opening[1]) == "1H"


class TestAuctionCompletion:
    def test_four_passes(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        for _ in range(3):
            auction.add_bid(Bid.make_pass())
            assert not auction.is_complete
        auction.add_bid(Bid.make_pass())
        assert auction.is_complete

    def test_three_passes_after_bid(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.make_pass())
        auction.add_bid(Bid.make_pass())
        assert not auction.is_complete
        auction.add_bid(Bid.make_pass())
        assert auction.is_complete

    def test_not_complete_with_bids_ongoing(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.make_pass())
        auction.add_bid(Bid.suit_bid(2, Strain.HEARTS))
        auction.add_bid(Bid.make_pass())
        assert not auction.is_complete

    def test_bid_after_complete_raises(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        for _ in range(4):
            auction.add_bid(Bid.make_pass())
        with pytest.raises(IllegalBidError, match="already complete"):
            auction.add_bid(Bid.make_pass())


class TestAuctionLegality:
    def test_lower_bid_raises(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(2, Strain.CLUBS))
        with pytest.raises(IllegalBidError, match="not higher"):
            auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))

    def test_same_bid_raises(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        with pytest.raises(IllegalBidError, match="not higher"):
            auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))

    def test_higher_bid_ok(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.suit_bid(1, Strain.SPADES))  # should not raise

    def test_double_opponents_bid(self) -> None:
        # N opens 1H, E doubles (opponent doubling)
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.double())  # East doubles North's bid — legal

    def test_cannot_double_own_bid(self) -> None:
        # N opens 1H, E passes, S tries to double partner's bid
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.make_pass())
        with pytest.raises(IllegalBidError, match="own side"):
            auction.add_bid(Bid.double())

    def test_cannot_double_nothing(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        with pytest.raises(IllegalBidError, match="no bid to double"):
            auction.add_bid(Bid.double())

    def test_cannot_double_twice(self) -> None:
        # N opens 1H, E doubles, S passes, W tries to double again
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.double())
        auction.add_bid(Bid.make_pass())
        with pytest.raises(IllegalBidError, match="already doubled"):
            auction.add_bid(Bid.double())

    def test_redouble_after_double(self) -> None:
        # N opens 1H, E doubles, S redoubles
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.double())
        auction.add_bid(Bid.redouble())  # should not raise

    def test_cannot_double_after_redouble(self) -> None:
        # N opens 1H, E doubles, S redoubles, W tries to double again
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.double())
        auction.add_bid(Bid.redouble())
        with pytest.raises(IllegalBidError, match="already doubled"):
            auction.add_bid(Bid.double())

    def test_cannot_redouble_without_double(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))
        auction.add_bid(Bid.make_pass())
        with pytest.raises(IllegalBidError, match="not doubled"):
            auction.add_bid(Bid.redouble())


class TestAuctionQueries:
    def test_bids_by(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))  # N
        auction.add_bid(Bid.make_pass())  # E
        auction.add_bid(Bid.suit_bid(2, Strain.HEARTS))  # S
        auction.add_bid(Bid.make_pass())  # W

        north_bids = auction.bids_by(Seat.NORTH)
        assert len(north_bids) == 1
        assert str(north_bids[0]) == "1H"

    def test_partner_last_bid(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))  # N
        auction.add_bid(Bid.make_pass())  # E
        # South's partner is North, who bid 1H
        assert auction.partner_last_bid(Seat.SOUTH) is not None
        assert str(auction.partner_last_bid(Seat.SOUTH)) == "1H"

    def test_rho_last_bid(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))  # N
        auction.add_bid(Bid.suit_bid(1, Strain.SPADES))  # E
        # South's RHO is East, who bid 1S
        assert auction.rho_last_bid(Seat.SOUTH) is not None
        assert str(auction.rho_last_bid(Seat.SOUTH)) == "1S"

    def test_is_competitive(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Strain.HEARTS))  # N opens
        auction.add_bid(Bid.make_pass())  # E passes
        assert not auction.is_competitive()

        auction.add_bid(Bid.suit_bid(2, Strain.HEARTS))  # S raises
        auction.add_bid(Bid.suit_bid(2, Strain.SPADES))  # W overcalls
        assert auction.is_competitive()

    def test_bids_property(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(parse_bid("P"))
        bids = auction.bids
        assert len(bids) == 2
        assert bids[0] == (Seat.NORTH, parse_bid("1H"))
        assert bids[1] == (Seat.EAST, parse_bid("P"))
