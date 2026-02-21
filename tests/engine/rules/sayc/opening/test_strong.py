"""Tests for strong 2C opening bid rule — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.opening.strong import Open2C
from bridge.model.auction import AuctionState, Seat
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str) -> BiddingContext:
    """Build a BiddingContext for an opening decision (dealer, no bids)."""
    return BiddingContext(
        Board(
            hand=Hand.from_pbn(pbn),
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
    )


class TestOpen2C:
    rule = Open2C()

    def test_strong_balanced(self):
        """SAYC: 22+ HCP opens 2C."""
        # AKQJ=10, AKQ=9, AJ8=5, A84=4 → 28 HCP, 4-3-3-3
        ctx = _ctx("AKQJ.AKQ.AJ8.A84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"
        assert result.rule_name == "opening.2c"
        assert result.forcing is True
        assert "Artificial" in result.alerts[0]

    def test_strong_balanced_5332(self):
        """SAYC: strong balanced opens 2C (rebids 2NT later)."""
        # AKQJT=10, AKQ=9, AK8=7, 84=0 → 26 HCP, 5-3-3-2
        ctx = _ctx("AKQJT.AKQ.AK8.84")
        assert self.rule.applies(ctx)

    def test_strong_unbalanced(self):
        """SAYC: 22+ HCP unbalanced opens 2C."""
        # AKQ=9, K3=3, AKQJT84=10, 4=0 → 22 HCP, 3-2-7-1
        ctx = _ctx("AKQ.K3.AKQJT84.4")
        assert self.rule.applies(ctx)

    def test_21_hcp_no_length_points(self):
        """21 HCP without length points doesn't reach 22 total."""
        # AKQ3=9, KQ3=5, AJ8=5, Q84=2 → 21 HCP, 4-3-3-3, total=21
        ctx = _ctx("AKQ3.KQ3.AJ8.Q84")
        assert not self.rule.applies(ctx)

    def test_20_hcp_with_length_reaches_22(self):
        """20 HCP + 2 length points = 22 total, qualifies."""
        # AKJT32=8, AKQ=9, K8=3, 84=0 → 20 HCP, 6-3-2-2, +2 length = 22
        ctx = _ctx("AKJT32.AKQ.K8.84")
        assert self.rule.applies(ctx)

    def test_19_hcp_with_length_too_low(self):
        """19 HCP + 1 length point = 20 total, doesn't qualify."""
        # AKJT3=8, AKQ=9, Q84=2, 84=0 → 19 HCP, 5-3-3-2, +1 length = 20
        ctx = _ctx("AKJT3.AKQ.Q84.84")
        assert not self.rule.applies(ctx)
