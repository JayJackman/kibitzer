"""Tests for parse_auction function."""

import pytest

from bridge.model.auction import (
    NO_VULNERABILITY,
    NS_VULNERABLE,
    IllegalBidError,
    Seat,
    parse_auction,
)
from bridge.model.bid import DOUBLE, REDOUBLE, SuitBid
from bridge.model.card import Suit


class TestParseAuction:
    def test_empty_string(self) -> None:
        auction = parse_auction("")
        assert auction.dealer == Seat.NORTH
        assert len(auction.bids) == 0
        assert auction.current_seat == Seat.NORTH

    def test_single_bid(self) -> None:
        auction = parse_auction("1H")
        assert len(auction.bids) == 1
        seat, bid = auction.bids[0]
        assert seat == Seat.NORTH
        assert bid == SuitBid(1, Suit.HEARTS)

    def test_full_auction(self) -> None:
        auction = parse_auction("1H P 2H P P P")
        assert auction.is_complete
        assert len(auction.bids) == 6

    def test_custom_dealer(self) -> None:
        auction = parse_auction("1H P", dealer=Seat.EAST)
        assert auction.dealer == Seat.EAST
        assert auction.bids[0][0] == Seat.EAST
        assert auction.bids[1][0] == Seat.SOUTH

    def test_with_vulnerability(self) -> None:
        auction = parse_auction("1H", vulnerability=NS_VULNERABLE)
        assert auction.vulnerability == NS_VULNERABLE

    def test_default_vulnerability(self) -> None:
        auction = parse_auction("1H")
        assert auction.vulnerability == NO_VULNERABILITY

    def test_invalid_bid_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid suit in bid"):
            parse_auction("1Z")

    def test_illegal_sequence_raises(self) -> None:
        with pytest.raises(IllegalBidError, match="not higher"):
            parse_auction("2H 1C")

    def test_double_and_redouble(self) -> None:
        auction = parse_auction("1H X XX")
        assert len(auction.bids) == 3
        assert auction.bids[1][1] == DOUBLE
        assert auction.bids[2][1] == REDOUBLE

    def test_passed_out(self) -> None:
        auction = parse_auction("P P P P")
        assert auction.is_complete
        contract = auction.contract
        assert contract is not None
        assert contract.passed_out

    def test_case_insensitive(self) -> None:
        auction = parse_auction("1h p 2H PASS")
        assert len(auction.bids) == 4

    def test_extra_whitespace(self) -> None:
        auction = parse_auction("  1H   P   2H  ")
        assert len(auction.bids) == 3
