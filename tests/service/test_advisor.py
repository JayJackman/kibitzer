"""Tests for BiddingAdvisor."""

from bridge.engine.rule import Category
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, SuitBid, parse_bid
from bridge.model.card import Suit
from bridge.model.hand import Hand
from bridge.service.advisor import BiddingAdvisor


class TestBiddingAdvisor:
    def test_advise_opening_hand(self) -> None:
        """17 HCP balanced -> recommended 1NT, phase OPENING."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AK32.KQ3.J84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        advice = advisor.advise(hand, auction)
        assert advice.recommended.bid == SuitBid(1, Suit.NOTRUMP)
        assert advice.phase == Category.OPENING
        assert advice.hand_evaluation.hcp == 17
        assert advice.hand_evaluation.is_balanced

    def test_advise_response_hand(self) -> None:
        """Response to 1H with 15 HCP and 5 spades -> 1S."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AKJ52.Q73.84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        advice = advisor.advise(hand, auction)
        assert advice.recommended.bid == SuitBid(1, Suit.SPADES)
        assert advice.phase == Category.RESPONSE

    def test_advise_includes_alternatives(self) -> None:
        """Alternatives list is populated and excludes the winner."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AKJ52.Q73.84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        advice = advisor.advise(hand, auction)
        winner_name = advice.recommended.rule_name
        assert all(alt.rule_name != winner_name for alt in advice.alternatives)

    def test_advise_hand_evaluation_populated(self) -> None:
        """HandEvaluation has all expected fields."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AK32.KQ3.J84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        advice = advisor.advise(hand, auction)
        ev = advice.hand_evaluation
        assert ev.hcp == 17
        assert ev.shape == (4, 3, 3, 3)
        assert ev.is_balanced
        assert ev.quick_tricks > 0
        assert ev.total_points >= ev.hcp
        assert ev.losers >= 0
        assert ev.controls >= 0

    def test_advise_weak_hand_passes(self) -> None:
        """Weak hand with no opening -> Pass."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("8765.432.J84.973")
        auction = AuctionState(dealer=Seat.NORTH)
        advice = advisor.advise(hand, auction)
        assert advice.recommended.bid == PASS
        assert advice.phase == Category.OPENING

    def test_advise_seat_inferred_from_auction(self) -> None:
        """Seat is inferred from auction.current_seat, not passed explicitly."""
        advisor = BiddingAdvisor()
        hand = Hand.from_pbn("AK32.KQ3.J84.A73")
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(PASS)  # N passes
        auction.add_bid(PASS)  # E passes
        # Now it's South's turn
        assert auction.current_seat == Seat.SOUTH
        advice = advisor.advise(hand, auction)
        assert advice.phase == Category.OPENING
