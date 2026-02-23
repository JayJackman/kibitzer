"""Tests for Table."""

import pytest

from bridge.model.auction import IllegalBidError, Seat
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit
from bridge.model.hand import Hand
from bridge.service.models import (
    AuctionCompleteError,
    DuplicateCardError,
    HandNotSetError,
    NotYourTurnError,
    Player,
    PlayerNotSeatedError,
    SeatEmptyError,
    SeatOccupiedError,
    TableStatus,
    UnauthorizedBidError,
)
from bridge.service.table import Table

# -- Fixtures --

ALICE = Player(name="Alice")
BOB = Player(name="Bob")
CAROL = Player(name="Carol")
DAVE = Player(name="Dave")

HAND_N = Hand.from_pbn("AK32.KQ3.J84.A73")
HAND_E = Hand.from_pbn("Q54.J984.AK3.Q82")
HAND_S = Hand.from_pbn("JT9.AT2.Q972.KJ4")
HAND_W = Hand.from_pbn("876.765.T65.T965")


def _seated_table() -> Table:
    """Table with all 4 players seated."""
    table = Table(table_id="test")
    table.join(Seat.NORTH, ALICE)
    table.join(Seat.EAST, BOB)
    table.join(Seat.SOUTH, CAROL)
    table.join(Seat.WEST, DAVE)
    return table


def _ready_table() -> Table:
    """Table with all 4 players seated and hands set."""
    table = _seated_table()
    table.set_hand(Seat.NORTH, HAND_N)
    table.set_hand(Seat.EAST, HAND_E)
    table.set_hand(Seat.SOUTH, HAND_S)
    table.set_hand(Seat.WEST, HAND_W)
    return table


class TestJoinLeave:
    def test_join(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        assert table.seats[Seat.NORTH] == ALICE

    def test_join_occupied_seat_raises(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        with pytest.raises(SeatOccupiedError, match="NORTH"):
            table.join(Seat.NORTH, BOB)

    def test_leave(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        table.leave(Seat.NORTH)
        assert table.seats[Seat.NORTH] is None

    def test_leave_empty_seat_raises(self) -> None:
        table = Table(table_id="t1")
        with pytest.raises(SeatEmptyError, match="NORTH"):
            table.leave(Seat.NORTH)


class TestSetHand:
    def test_set_hand(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        table.set_hand(Seat.NORTH, HAND_N)
        assert table.hands[Seat.NORTH] == HAND_N

    def test_set_hand_unseated_raises(self) -> None:
        table = Table(table_id="t1")
        with pytest.raises(SeatEmptyError, match="NORTH"):
            table.set_hand(Seat.NORTH, HAND_N)

    def test_set_hand_duplicate_card_raises(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        table.join(Seat.EAST, BOB)
        table.set_hand(Seat.NORTH, HAND_N)
        # Use the same hand (same cards) for East -> conflict
        with pytest.raises(DuplicateCardError, match="NORTH.*EAST|EAST.*NORTH"):
            table.set_hand(Seat.EAST, HAND_N)


class TestMakeBid:
    def test_valid_bid(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.NOTRUMP), ALICE)
        assert len(table.auction.bids) == 1

    def test_wrong_turn_raises(self) -> None:
        table = _ready_table()
        with pytest.raises(NotYourTurnError, match="NORTH"):
            table.make_bid(Seat.EAST, SuitBid(1, Suit.HEARTS), BOB)

    def test_illegal_bid_raises(self) -> None:
        """Illegal bid (e.g., 1C after 2C) raises."""
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(2, Suit.CLUBS), ALICE)
        with pytest.raises(IllegalBidError):
            table.make_bid(Seat.EAST, SuitBid(1, Suit.HEARTS), BOB)

    def test_proxy_bid_for_unoccupied_seat(self) -> None:
        """Any seated player can bid for unoccupied seats."""
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        # East is unoccupied. Alice (seated at North) bids for North first.
        table.set_hand(Seat.NORTH, HAND_N)
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.NOTRUMP), ALICE)
        # Now it's East's turn, but East has no player. Alice can proxy.
        table.make_bid(Seat.EAST, PASS, ALICE)

    def test_bid_for_another_players_seat_raises(self) -> None:
        table = _seated_table()
        with pytest.raises(UnauthorizedBidError, match="NORTH.*Alice"):
            table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), BOB)

    def test_bid_by_unseated_player_raises(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        eve = Player(name="Eve")
        with pytest.raises(PlayerNotSeatedError, match="Eve"):
            table.make_bid(Seat.NORTH, PASS, eve)


class TestGetState:
    def test_shows_only_your_hand(self) -> None:
        table = _ready_table()
        view = table.get_state(Seat.NORTH)
        assert view.hand == HAND_N
        assert view.seat == Seat.NORTH

    def test_shows_all_seat_assignments(self) -> None:
        table = _ready_table()
        view = table.get_state(Seat.NORTH)
        assert view.seats[Seat.NORTH] == ALICE
        assert view.seats[Seat.EAST] == BOB

    def test_shows_all_bids(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.NOTRUMP), ALICE)
        table.make_bid(Seat.EAST, PASS, BOB)
        view = table.get_state(Seat.SOUTH)
        assert len(view.bids) == 2


class TestGetAdvice:
    def test_get_advice(self) -> None:
        table = _ready_table()
        advice = table.get_advice(Seat.NORTH)
        assert advice.recommended.bid == SuitBid(1, Suit.NOTRUMP)

    def test_not_your_turn_raises(self) -> None:
        table = _ready_table()
        with pytest.raises(NotYourTurnError):
            table.get_advice(Seat.EAST)

    def test_no_hand_raises(self) -> None:
        table = Table(table_id="t1")
        table.join(Seat.NORTH, ALICE)
        with pytest.raises(HandNotSetError, match="NORTH"):
            table.get_advice(Seat.NORTH)


class TestStatusTransitions:
    def test_initial_status_waiting(self) -> None:
        table = Table(table_id="t1")
        assert table.status == TableStatus.WAITING

    def test_first_bid_transitions_to_in_progress(self) -> None:
        table = _ready_table()
        assert table.status == TableStatus.WAITING
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        assert table.status == TableStatus.IN_PROGRESS

    def test_auction_complete_transitions_to_completed(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.make_bid(Seat.EAST, PASS, BOB)
        table.make_bid(Seat.SOUTH, PASS, CAROL)
        table.make_bid(Seat.WEST, PASS, DAVE)
        assert table.status == TableStatus.COMPLETED

    def test_completed_shows_contract(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.make_bid(Seat.EAST, PASS, BOB)
        table.make_bid(Seat.SOUTH, PASS, CAROL)
        table.make_bid(Seat.WEST, PASS, DAVE)
        view = table.get_state(Seat.NORTH)
        assert view.contract is not None
        assert view.contract.level == 1
        assert view.contract.suit == Suit.HEARTS

    def test_bid_after_complete_raises(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.make_bid(Seat.EAST, PASS, BOB)
        table.make_bid(Seat.SOUTH, PASS, CAROL)
        table.make_bid(Seat.WEST, PASS, DAVE)
        with pytest.raises(AuctionCompleteError):
            table.make_bid(Seat.NORTH, PASS, ALICE)

    def test_advice_after_complete_raises(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.make_bid(Seat.EAST, PASS, BOB)
        table.make_bid(Seat.SOUTH, PASS, CAROL)
        table.make_bid(Seat.WEST, PASS, DAVE)
        with pytest.raises(AuctionCompleteError):
            table.get_advice(Seat.NORTH)


class TestReset:
    def test_reset_keeps_seats(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.reset()
        assert table.seats[Seat.NORTH] == ALICE
        assert table.seats[Seat.EAST] == BOB

    def test_reset_clears_hands(self) -> None:
        table = _ready_table()
        table.reset()
        for hand in table.hands.values():
            assert hand is None

    def test_reset_clears_auction(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        table.reset()
        assert len(table.auction.bids) == 0

    def test_reset_back_to_waiting(self) -> None:
        table = _ready_table()
        table.make_bid(Seat.NORTH, SuitBid(1, Suit.HEARTS), ALICE)
        assert table.status == TableStatus.IN_PROGRESS
        table.reset()
        assert table.status == TableStatus.WAITING
