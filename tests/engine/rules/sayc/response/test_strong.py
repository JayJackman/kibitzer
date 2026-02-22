"""Tests for responses to 2C opening -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.response.strong import (
    Respond2DWaiting,
    Respond2NTOver2C,
    RespondPositiveSuitOver2C,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str) -> BiddingContext:
    """Build a BiddingContext where partner opened 2C and responder acts.

    North opens 2C, East passes, South (responder) acts.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("2C"))  # Partner (N) opens 2C
    auction.add_bid(PASS)  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# -- Respond2NTOver2C ---------------------------------------------------------


class TestRespond2NTOver2C:
    rule = Respond2NTOver2C()

    def test_8_hcp_balanced(self) -> None:
        """8 HCP, balanced -> 2NT positive."""
        # 9 HCP, 3-3-3-4 balanced
        ctx = _ctx("KJ3.Q42.K43.5432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_7_hcp_balanced_rejected(self) -> None:
        """7 HCP, balanced -> too weak for 2NT positive."""
        # 7 HCP, 3-3-3-4 balanced
        ctx = _ctx("KQ3.J42.J32.5432")
        assert not self.rule.applies(ctx)

    def test_unbalanced_rejected(self) -> None:
        """10 HCP, unbalanced -> not 2NT."""
        # KQ432.K43.2.Q432 = K=3+Q=2+K=3+Q=2 = 10 HCP, 5-3-1-4 unbalanced
        ctx = _ctx("KQ432.K43.2.Q432")
        assert not self.rule.applies(ctx)

    def test_not_after_1nt(self) -> None:
        """Rule does not apply after 1NT opening."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1NT"))
        auction.add_bid(PASS)
        hand = Hand.from_pbn("KJ3.Q42.K43.5432")
        ctx = BiddingContext(Board(hand=hand, seat=Seat.SOUTH, auction=auction))
        assert not self.rule.applies(ctx)


# -- RespondPositiveSuitOver2C ------------------------------------------------


class TestRespondPositiveSuitOver2C:
    rule = RespondPositiveSuitOver2C()

    def test_5_hearts_with_ak(self) -> None:
        """8+ HCP, 5 hearts with AK -> 2H positive."""
        # 10 HCP, 5 hearts with AK
        ctx = _ctx("5432.AK432.K4.32")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_5_spades_with_aq(self) -> None:
        """8+ HCP, 5 spades with AQ -> 2S positive."""
        # AQ432.543.K4.432 = A=4+Q=2+K=3 = 9 HCP, 5 spades with AQ
        ctx = _ctx("AQ432.543.K4.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_5_diamonds_with_kq(self) -> None:
        """8+ HCP, 5 diamonds with KQ -> 3D positive."""
        # 5432.K43.KQ432.2 = K=3+K=3+Q=2 = 8 HCP, 5 diamonds with KQ
        ctx = _ctx("5432.K43.KQ432.2")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_5_clubs_with_ak(self) -> None:
        """8+ HCP, 5 clubs with AK -> 3C positive."""
        # 5432.K43.2.AK432 = K=3+A=4+K=3 = 10 HCP, 5 clubs with AK
        ctx = _ctx("5432.K43.2.AK432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_only_one_honor_rejected(self) -> None:
        """8+ HCP, 5+ suit but only 1 of top 3 -> no positive suit."""
        # AJ432.K43.Q32.32 = A=4+J=1+K=3+Q=2 = 10 HCP, 5 spades but only A (1 of top 3)
        ctx = _ctx("AJ432.K43.Q32.32")
        assert not self.rule.applies(ctx)

    def test_7_hcp_rejected(self) -> None:
        """7 HCP with quality suit -> too weak."""
        # 7 HCP, 5 spades with AK
        ctx = _ctx("AK432.543.432.32")
        assert not self.rule.applies(ctx)

    def test_4_card_suit_rejected(self) -> None:
        """8+ HCP, only 4-card suit -> no positive suit."""
        # AK43.5432.K32.32 = A=4+K=3+K=3 = 10 HCP, 4 spades (not 5+)
        ctx = _ctx("AK43.5432.K32.32")
        assert not self.rule.applies(ctx)

    def test_picks_longest_suit(self) -> None:
        """With two qualifying suits, picks the longer one."""
        # AK432.AQ5432.2.2 = A=4+K=3+A=4+Q=2 = 13 HCP, 6H > 5S
        ctx = _ctx("AK432.AQ5432.2.2")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"  # 6 hearts > 5 spades

    def test_equal_length_picks_higher(self) -> None:
        """With equal-length qualifying suits, picks higher rank."""
        # AK432.AQ432.32.2 = A=4+K=3+A=4+Q=2 = 13 HCP, 5S = 5H -> spades
        ctx = _ctx("AK432.AQ432.32.2")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"  # higher rank wins


# -- Respond2DWaiting ---------------------------------------------------------


class TestRespond2DWaiting:
    rule = Respond2DWaiting()

    def test_weak_hand(self) -> None:
        """0 HCP -> 2D waiting."""
        # 5432.5432.5432.5 = 0 HCP
        ctx = _ctx("5432.5432.5432.5")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_strong_hand_also_applies(self) -> None:
        """Strong hand also qualifies for 2D (catch-all), though positive wins."""
        # AK432.AQ432.32.2 = 13 HCP with quality suits
        ctx = _ctx("AK432.AQ432.32.2")
        assert self.rule.applies(ctx)

    def test_not_after_1nt(self) -> None:
        """Rule does not apply after 1NT opening."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1NT"))
        auction.add_bid(PASS)
        hand = Hand.from_pbn("5432.5432.5432.5")
        ctx = BiddingContext(Board(hand=hand, seat=Seat.SOUTH, auction=auction))
        assert not self.rule.applies(ctx)


# -- Priority conflicts -------------------------------------------------------


class TestPriorityConflicts2C:
    """Verify priority ordering resolves ambiguities correctly."""

    def test_balanced_8_hcp_prefers_2nt_over_positive_suit(self) -> None:
        """8+ HCP, balanced, 5+ quality suit -> 2NT wins over positive suit."""
        # AQ432.K43.Q43.32 = A=4+Q=2+K=3+Q=2 = 11 HCP, balanced, 5S with AQ
        r2nt = Respond2NTOver2C()
        rsuit = RespondPositiveSuitOver2C()
        ctx = _ctx("AQ432.K43.Q43.32")
        assert r2nt.applies(ctx)
        assert rsuit.applies(ctx)
        assert r2nt.priority > rsuit.priority

    def test_balanced_8_hcp_prefers_2nt_over_2d(self) -> None:
        """8+ HCP, balanced -> 2NT wins over 2D waiting."""
        r2nt = Respond2NTOver2C()
        r2d = Respond2DWaiting()
        ctx = _ctx("KJ3.Q42.K43.5432")
        assert r2nt.applies(ctx)
        assert r2d.applies(ctx)
        assert r2nt.priority > r2d.priority

    def test_positive_suit_prefers_over_2d(self) -> None:
        """8+ HCP, quality suit -> positive suit wins over 2D."""
        rsuit = RespondPositiveSuitOver2C()
        r2d = Respond2DWaiting()
        ctx = _ctx("AQ432.543.K4.432")
        assert rsuit.applies(ctx)
        assert r2d.applies(ctx)
        assert rsuit.priority > r2d.priority
