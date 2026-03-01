"""Unit tests for PracticeSession -- exercises the full lifecycle without HTTP."""

from __future__ import annotations

import random

import pytest

from bridge.api.practice.session import (
    AlreadySeatedError,
    AuctionCompleteError,
    BidResult,
    PlayerNotFoundError,
    PracticeSession,
    PracticeState,
    SeatOccupiedError,
    SessionMode,
    compute_legal_bids,
)
from bridge.api.practice.state import (
    clear_all,
    create_session,
    get_session,
    get_session_by_code,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit
from bridge.service.advisor import BiddingAdvisor


@pytest.fixture()
def advisor() -> BiddingAdvisor:
    return BiddingAdvisor()


@pytest.fixture()
def session(advisor: BiddingAdvisor) -> PracticeSession:
    """A session with a fixed seed so results are deterministic."""
    return PracticeSession(
        user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(42)
    )


# ── Construction ─────────────────────────────────────────────


class TestConstruction:
    def test_session_has_id(self, session: PracticeSession) -> None:
        assert len(session.id) == 12

    def test_host_user_id(self, session: PracticeSession) -> None:
        assert session.host_user_id == 1

    def test_player_seated(self, session: PracticeSession) -> None:
        assert session.players[Seat.SOUTH] == 1
        # Other seats are computer-controlled.
        assert session.players[Seat.NORTH] is None
        assert session.players[Seat.EAST] is None
        assert session.players[Seat.WEST] is None

    def test_four_hands_dealt(self, session: PracticeSession) -> None:
        assert len(session.hands) == 4
        for seat in Seat:
            assert len(session.hands[seat].cards) == 13

    def test_no_duplicate_cards_across_hands(self, session: PracticeSession) -> None:
        all_cards = set()
        for hand in session.hands.values():
            all_cards.update(hand.cards)
        assert len(all_cards) == 52

    def test_hand_number_starts_at_1(self, session: PracticeSession) -> None:
        assert session.hand_number == 1


# ── seat_for ─────────────────────────────────────────────────


class TestSeatFor:
    def test_finds_seated_user(self, session: PracticeSession) -> None:
        assert session.seat_for(1) == Seat.SOUTH

    def test_raises_for_unknown_user(self, session: PracticeSession) -> None:
        with pytest.raises(PlayerNotFoundError):
            session.seat_for(999)


# ── get_state ────────────────────────────────────────────────


class TestGetState:
    def test_returns_practice_state(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        assert isinstance(state, PracticeState)

    def test_state_shows_player_hand(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        assert state.hand == session.hands[Seat.SOUTH]

    def test_state_shows_seat(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        assert state.your_seat == Seat.SOUTH

    def test_state_has_hand_evaluation(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        assert state.hand_evaluation.hcp >= 0

    def test_legal_bids_when_my_turn(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        if state.is_my_turn:
            assert len(state.legal_bids) > 0
            assert "Pass" in state.legal_bids

    def test_no_legal_bids_when_not_my_turn(self, advisor: BiddingAdvisor) -> None:
        """When the human is South but dealer is North, computer bids first.
        If the computer hasn't passed to South yet, is_my_turn could be False.
        We test the scenario where auction completes before the human's turn."""
        # Just verify the field: when auction is complete, legal_bids is empty.
        session = PracticeSession(
            user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(42)
        )
        # Drive the auction to completion by bidding passes.
        while not session.auction.is_complete:
            if session.auction.current_seat == Seat.SOUTH:
                session.place_bid(1, "Pass")
            # Computer seats handle themselves.
        state = session.get_state(1)
        assert state.legal_bids == []

    def test_all_hands_hidden_during_bidding(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        if not state.auction.is_complete:
            assert state.all_hands is None

    def test_all_hands_revealed_when_complete(self, advisor: BiddingAdvisor) -> None:
        session = PracticeSession(
            user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(42)
        )
        # Pass until auction completes.
        while not session.auction.is_complete:
            if session.auction.current_seat == Seat.SOUTH:
                session.place_bid(1, "Pass")
        state = session.get_state(1)
        assert state.all_hands is not None
        assert len(state.all_hands) == 4


# ── place_bid ────────────────────────────────────────────────


class TestPlaceBid:
    def test_pass_returns_bid_result(self, session: PracticeSession) -> None:
        # Advance to the human's turn if needed.
        if session.auction.current_seat != Seat.SOUTH:
            pytest.skip("Computer bids didn't reach South")
        result = session.place_bid(1, "Pass")
        assert isinstance(result, BidResult)

    def test_bid_result_has_engine_recommendation(
        self, session: PracticeSession
    ) -> None:
        if session.auction.current_seat != Seat.SOUTH:
            pytest.skip("Computer bids didn't reach South")
        result = session.place_bid(1, "Pass")
        assert isinstance(result.engine_bid, str)
        assert isinstance(result.engine_explanation, str)

    def test_matched_engine_when_same_bid(self, advisor: BiddingAdvisor) -> None:
        """Place the engine's own recommendation -- matched_engine should be True."""
        session = PracticeSession(
            user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(42)
        )
        if session.auction.current_seat != Seat.SOUTH:
            pytest.skip("Not South's turn after construction")
        advice = session.get_advice(1)
        bid_str = _bid_to_str(advice.recommended.bid)
        result = session.place_bid(1, bid_str)
        assert result.matched_engine is True

    def test_wrong_user_raises(self, session: PracticeSession) -> None:
        with pytest.raises(PlayerNotFoundError):
            session.place_bid(999, "Pass")

    def test_illegal_bid_raises(self, session: PracticeSession) -> None:
        """A bid lower than the current contract should fail."""
        if session.auction.current_seat != Seat.SOUTH:
            pytest.skip("Not South's turn")
        # Place a valid bid first.
        session.place_bid(1, "7NT")
        # Now the auction should still be going -- if it's South's turn
        # again, try a lower bid.
        if (
            not session.auction.is_complete
            and session.auction.current_seat == Seat.SOUTH
        ):
            from bridge.model.auction import IllegalBidError

            with pytest.raises(IllegalBidError):
                session.place_bid(1, "1C")

    def test_bid_after_complete_raises(self, advisor: BiddingAdvisor) -> None:
        session = PracticeSession(
            user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(42)
        )
        while not session.auction.is_complete:
            if session.auction.current_seat == Seat.SOUTH:
                session.place_bid(1, "Pass")
        with pytest.raises(AuctionCompleteError):
            session.place_bid(1, "Pass")


# ── get_advice ───────────────────────────────────────────────


class TestGetAdvice:
    def test_returns_bidding_advice(self, session: PracticeSession) -> None:
        advice = session.get_advice(1)
        assert advice.recommended.bid is not None

    def test_wrong_user_raises(self, session: PracticeSession) -> None:
        with pytest.raises(PlayerNotFoundError):
            session.get_advice(999)


# ── redeal ───────────────────────────────────────────────────


class TestRedeal:
    def test_hand_number_increments(self, session: PracticeSession) -> None:
        session.redeal()
        assert session.hand_number == 2

    def test_new_hands_dealt(self, session: PracticeSession) -> None:
        old_cards = session.hands[Seat.SOUTH].cards
        session.redeal()
        new_cards = session.hands[Seat.SOUTH].cards
        # With 52! permutations, identical deals are astronomically unlikely.
        assert old_cards != new_cards

    def test_dealer_rotates(self, session: PracticeSession) -> None:
        first_dealer = session.auction.dealer
        session.redeal()
        expected = Seat((first_dealer.value + 1) % 4)
        assert session.auction.dealer == expected

    def test_auction_resets(self, session: PracticeSession) -> None:
        session.redeal()
        assert not session.auction.is_complete

    def test_feedback_cleared(self, session: PracticeSession) -> None:
        session.redeal()
        state = session.get_state(1)
        assert state.last_feedback is None

    def test_multiple_redeals_rotate_through_all_seats(
        self, session: PracticeSession
    ) -> None:
        dealers = [session.auction.dealer]
        for _ in range(4):
            session.redeal()
            dealers.append(session.auction.dealer)
        # After 4 redeals, dealer should be back to the original.
        assert dealers[0] == dealers[4]


# ── compute_legal_bids ───────────────────────────────────────


class TestComputeLegalBids:
    def test_fresh_auction_has_all_bids(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        legal = compute_legal_bids(auction)
        # 35 suit bids (7 levels * 5 suits) + Pass = 36.
        # No double or redouble at start.
        assert len(legal) == 36
        assert "Pass" in legal
        assert "1C" in legal
        assert "7NT" in legal
        assert "X" not in legal
        assert "XX" not in legal

    def test_after_1h_only_higher_bids_legal(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))
        legal = compute_legal_bids(auction)
        assert "1C" not in legal
        assert "1D" not in legal
        assert "1H" not in legal
        assert "1S" in legal
        assert "1NT" in legal
        assert "2C" in legal
        assert "Pass" in legal

    def test_double_available_after_opponent_bid(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # North
        # East's turn -- opponent's bid, so double is legal.
        legal = compute_legal_bids(auction)
        assert "X" in legal

    def test_no_double_on_own_side(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # North
        auction.add_bid(PASS)  # East
        # South's turn -- partner bid, no double.
        legal = compute_legal_bids(auction)
        assert "X" not in legal

    def test_redouble_after_double(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(SuitBid(1, Suit.HEARTS))  # North bids 1H
        from bridge.model.bid import DOUBLE

        auction.add_bid(DOUBLE)  # East doubles
        # South's turn -- can redouble partner's bid that was doubled.
        legal = compute_legal_bids(auction)
        assert "XX" in legal
        assert "X" not in legal  # Can't double again.


# ── SessionMode and join_code ────────────────────────────────


class TestSessionMode:
    def test_default_mode_is_practice(self, session: PracticeSession) -> None:
        assert session.mode == SessionMode.PRACTICE

    def test_join_code_generated(self, session: PracticeSession) -> None:
        assert len(session.join_code) == 6
        # All characters should be from the unambiguous set.
        allowed = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        assert all(c in allowed for c in session.join_code)

    def test_state_includes_mode_and_join_code(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        assert state.mode == SessionMode.PRACTICE
        assert state.join_code == session.join_code

    def test_state_includes_players(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        # South is human (empty string because test didn't provide username),
        # others are computer (None).
        assert state.players[Seat.SOUTH] == ""
        assert state.players[Seat.NORTH] is None
        assert state.players[Seat.EAST] is None
        assert state.players[Seat.WEST] is None

    def test_state_waiting_for(self, session: PracticeSession) -> None:
        state = session.get_state(1)
        if state.is_my_turn:
            assert state.waiting_for == Seat.SOUTH
        else:
            assert state.waiting_for is None


# ── join / leave / available_seats ──────────────────────────


class TestJoinLeave:
    def test_available_seats(self, session: PracticeSession) -> None:
        available = session.available_seats()
        assert Seat.SOUTH not in available
        assert len(available) == 3

    def test_join_seat(self, session: PracticeSession) -> None:
        session.join(2, Seat.NORTH, username="player2")
        assert session.players[Seat.NORTH] == 2
        assert Seat.NORTH not in session.available_seats()

    def test_join_with_username(self, session: PracticeSession) -> None:
        session.join(2, Seat.NORTH, username="player2")
        names = session._player_names()
        assert names[Seat.NORTH] == "player2"

    def test_join_occupied_seat_raises(self, session: PracticeSession) -> None:
        with pytest.raises(SeatOccupiedError):
            session.join(2, Seat.SOUTH)

    def test_join_already_seated_raises(self, session: PracticeSession) -> None:
        with pytest.raises(AlreadySeatedError):
            session.join(1, Seat.NORTH)

    def test_leave_reverts_to_computer(self, session: PracticeSession) -> None:
        session.join(2, Seat.NORTH, username="player2")
        session.leave(2)
        assert session.players[Seat.NORTH] is None
        assert Seat.NORTH in session.available_seats()

    def test_leave_not_seated_raises(self, session: PracticeSession) -> None:
        with pytest.raises(PlayerNotFoundError):
            session.leave(999)

    def test_join_after_leave(self, session: PracticeSession) -> None:
        session.join(2, Seat.NORTH, username="player2")
        session.leave(2)
        session.join(3, Seat.NORTH, username="player3")
        assert session.players[Seat.NORTH] == 3

    def test_multiple_humans_get_state(self, advisor: BiddingAdvisor) -> None:
        """Two humans can each get their own state view."""
        session = PracticeSession(
            user_id=1,
            seat=Seat.SOUTH,
            advisor=advisor,
            username="host",
            rng=random.Random(42),
        )
        session.join(2, Seat.NORTH, username="guest")
        state_s = session.get_state(1)
        state_n = session.get_state(2)
        assert state_s.your_seat == Seat.SOUTH
        assert state_n.your_seat == Seat.NORTH
        # Each sees their own hand.
        assert state_s.hand == session.hands[Seat.SOUTH]
        assert state_n.hand == session.hands[Seat.NORTH]

    def test_computer_stops_at_any_human(self, advisor: BiddingAdvisor) -> None:
        """Computer bids should stop at any human seat, not just the host."""
        session = PracticeSession(
            user_id=1,
            seat=Seat.SOUTH,
            advisor=advisor,
            username="host",
            rng=random.Random(42),
        )
        session.join(2, Seat.NORTH, username="guest")
        # The auction should be waiting for a human, not completed by computers.
        if not session.auction.is_complete:
            current = session.auction.current_seat
            assert session.players[current] is not None


# ── In-memory store ──────────────────────────────────────────


class TestSessionStore:
    def setup_method(self) -> None:
        clear_all()

    def test_create_and_get(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH)
        found = get_session(session.id)
        assert found is session

    def test_get_missing_returns_none(self) -> None:
        assert get_session("nonexistent") is None

    def test_delete(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH)
        from bridge.api.practice.state import delete_session

        delete_session(session.id)
        assert get_session(session.id) is None

    def test_delete_idempotent(self) -> None:
        from bridge.api.practice.state import delete_session

        delete_session("nonexistent")  # Should not raise.

    def test_join_code_indexed(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH)
        found = get_session_by_code(session.join_code)
        assert found is session

    def test_join_code_case_insensitive(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH)
        found = get_session_by_code(session.join_code.lower())
        assert found is session

    def test_join_code_missing(self) -> None:
        assert get_session_by_code("ZZZZZZ") is None

    def test_delete_removes_join_code(self) -> None:
        from bridge.api.practice.state import delete_session

        session = create_session(user_id=1, seat=Seat.SOUTH)
        code = session.join_code
        delete_session(session.id)
        assert get_session_by_code(code) is None

    def test_create_with_mode(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH, mode=SessionMode.PRACTICE)
        assert session.mode == SessionMode.PRACTICE

    def test_create_with_username(self) -> None:
        session = create_session(user_id=1, seat=Seat.SOUTH, username="testuser")
        names = session._player_names()
        assert names[Seat.SOUTH] == "testuser"


# ── Full lifecycle ───────────────────────────────────────────


class TestFullLifecycle:
    """End-to-end: create session, bid until complete, redeal."""

    def test_play_through_and_redeal(self, advisor: BiddingAdvisor) -> None:
        session = PracticeSession(
            user_id=1, seat=Seat.SOUTH, advisor=advisor, rng=random.Random(99)
        )

        # Play until auction completes (all passes scenario).
        turns = 0
        while not session.auction.is_complete:
            if session.auction.current_seat == Seat.SOUTH:
                result = session.place_bid(1, "Pass")
                assert isinstance(result, BidResult)
            turns += 1
            if turns > 50:
                pytest.fail("Auction did not complete within 50 turns")

        # Verify completion state.
        state = session.get_state(1)
        assert state.auction.is_complete
        assert state.all_hands is not None
        assert state.legal_bids == []
        assert state.is_my_turn is False

        # Redeal and verify fresh state.
        session.redeal()
        state2 = session.get_state(1)
        assert state2.hand_number == 2
        assert not state2.auction.is_complete
        assert state2.last_feedback is None


# ── Helpers ──────────────────────────────────────────────────


def _bid_to_str(bid: object) -> str:
    """Convert a Bid to a parseable string."""
    if hasattr(bid, "level") and hasattr(bid, "suit"):
        return f"{bid.level}{bid.suit.letter}"  # type: ignore[union-attr]
    return str(bid)
