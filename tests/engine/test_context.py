"""Tests for BiddingContext."""

from bridge.engine.context import BiddingContext
from bridge.model.auction import AuctionState, Seat, Vulnerability
from bridge.model.bid import Bid
from bridge.model.board import Board
from bridge.model.card import Suit
from bridge.model.hand import Hand

# Reuse test hands from Phase 2
BALANCED = Hand.from_pbn("AKJ52.KQ3.84.A73")  # 5-3-2-3, 17 HCP
YARBOROUGH = Hand.from_pbn("87654.432.T98.65")  # 5-3-3-2, 0 HCP


class TestBiddingContextFromBoard:
    def test_hand_metrics(self) -> None:
        board = Board(
            hand=BALANCED,
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)

        assert ctx.hcp == 17
        assert ctx.length_pts == 1
        assert ctx.total_pts == 18
        assert ctx.distribution_pts == 1
        assert ctx.controls == 6
        assert ctx.quick_tricks == 4.0
        assert ctx.ltc == 6

    def test_shape_helpers(self) -> None:
        board = Board(
            hand=BALANCED,
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)

        assert ctx.shape == (5, 3, 2, 3)
        assert ctx.sorted_shape == (5, 3, 3, 2)
        assert ctx.is_balanced  # sorted 5-3-3-2 is balanced
        assert ctx.is_semi_balanced
        assert ctx.longest_suit == Suit.SPADES

    def test_seat_and_vulnerability(self) -> None:
        vul = Vulnerability(ns_vulnerable=True)
        board = Board(
            hand=BALANCED,
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH, vulnerability=vul),
        )
        ctx = BiddingContext(board)

        assert ctx.seat == Seat.NORTH
        assert ctx.is_vulnerable

    def test_not_vulnerable(self) -> None:
        board = Board(
            hand=BALANCED,
            seat=Seat.EAST,
            auction=AuctionState(
                dealer=Seat.NORTH,
                vulnerability=Vulnerability(ns_vulnerable=True),
            ),
        )
        ctx = BiddingContext(board)
        assert not ctx.is_vulnerable

    def test_opening_position(self) -> None:
        board = Board(
            hand=BALANCED,
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)

        assert not ctx.has_opened
        assert ctx.opening_bid is None
        assert ctx.is_my_first_bid
        assert len(ctx.my_bids) == 0

    def test_after_partner_opens(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Suit.HEARTS))  # N opens 1H
        auction.add_bid(Bid.make_pass())  # E passes

        board = Board(hand=BALANCED, seat=Seat.SOUTH, auction=auction)
        ctx = BiddingContext(board)

        assert ctx.has_opened
        assert ctx.opening_bid is not None
        assert ctx.opening_bid[0] == Seat.NORTH
        assert ctx.partner_last_bid is not None
        assert str(ctx.partner_last_bid) == "1H"
        assert ctx.rho_last_bid is None
        assert ctx.is_my_first_bid

    def test_after_rho_overcalls(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Suit.HEARTS))  # N opens 1H
        auction.add_bid(Bid.suit_bid(1, Suit.SPADES))  # E overcalls 1S

        board = Board(hand=BALANCED, seat=Seat.SOUTH, auction=auction)
        ctx = BiddingContext(board)

        assert ctx.is_competitive
        assert ctx.rho_last_bid is not None
        assert str(ctx.rho_last_bid) == "1S"

    def test_my_bids_tracks_non_pass(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(Bid.suit_bid(1, Suit.HEARTS))  # N opens 1H
        auction.add_bid(Bid.make_pass())  # E
        auction.add_bid(Bid.suit_bid(2, Suit.HEARTS))  # S raises
        auction.add_bid(Bid.make_pass())  # W

        board = Board(hand=BALANCED, seat=Seat.NORTH, auction=auction)
        ctx = BiddingContext(board)

        assert len(ctx.my_bids) == 1
        assert str(ctx.my_bids[0]) == "1H"
        assert not ctx.is_my_first_bid

    def test_yarborough_metrics(self) -> None:
        board = Board(
            hand=YARBOROUGH,
            seat=Seat.SOUTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)

        assert ctx.hcp == 0
        assert ctx.total_pts == 1
        assert ctx.controls == 0
        assert ctx.quick_tricks == 0.0
        assert ctx.ltc == 11
