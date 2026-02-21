"""Tests for NT opening bid rules — SAYC 1NT (15-17) and 2NT (20-21)."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.opening.nt import Open1NT, Open2NT
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


# ── Open1NT ──────────────────────────────────────────────────────────


class TestOpen1NT:
    rule = Open1NT()

    def test_16_hcp_balanced_4333(self):
        """SAYC: 15-17 HCP balanced opens 1NT."""
        # AQ3=6, KJ84=4, QJ3=3, K84=3 → 16 HCP, 3-4-3-3
        ctx = _ctx("AQ3.KJ84.QJ3.K84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"
        assert result.rule_name == "opening.1nt"

    def test_17_hcp_balanced_4333(self):
        """SAYC: 17 HCP balanced opens 1NT."""
        # AK32=7, KQ3=5, J84=1, A73=4 → 17 HCP, 4-3-3-3
        ctx = _ctx("AK32.KQ3.J84.A73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"

    def test_17_hcp_balanced_5332_with_major(self):
        """SAYC: 5-3-3-2 is balanced; 5-card major OK in 1NT."""
        # AKJ52=8, KQ3=5, 84=0, A73=4 → 17 HCP, 5-3-2-3
        ctx = _ctx("AKJ52.KQ3.84.A73")
        assert self.rule.applies(ctx)

    def test_16_hcp_balanced_5332_with_minor(self):
        """SAYC: 5-card minor OK in 1NT."""
        # A93=4, K84=3, AQJ32=7, Q4=2 → 16 HCP, 3-3-5-2
        ctx = _ctx("A93.K84.AQJ32.Q4")
        assert self.rule.applies(ctx)

    def test_14_hcp_too_low(self):
        """14 HCP does not qualify for 1NT."""
        # AJ32=5, KJ8=4, Q84=2, K73=3 → 14 HCP, 4-3-3-3
        ctx = _ctx("AJ32.KJ8.Q84.K73")
        assert not self.rule.applies(ctx)

    def test_18_hcp_too_high(self):
        """18 HCP does not qualify for 1NT (opens 1-suit, rebids 2NT)."""
        # AKQ3=9, QJ8=3, A93=4, Q84=2 → 18 HCP, 4-3-3-3
        ctx = _ctx("AKQ3.QJ8.A93.Q84")
        assert not self.rule.applies(ctx)

    def test_17_hcp_unbalanced_rejected(self):
        """Unbalanced shape doesn't qualify even with right HCP."""
        # AKJ532=8, KQ3=5, 84=0, A7=4 → 17 HCP, 6-3-2-2 (not balanced)
        ctx = _ctx("AKJ532.KQ3.84.A7")
        assert not self.rule.applies(ctx)

    def test_5422_not_balanced(self):
        """5-4-2-2 is semi-balanced but not balanced for 1NT purposes."""
        # AKJ52=8, KQ84=5, 84=0, A7=4 → 17 HCP, 5-4-2-2
        ctx = _ctx("AKJ52.KQ84.84.A7")
        assert not self.rule.applies(ctx)


# ── Open2NT ──────────────────────────────────────────────────────────


class TestOpen2NT:
    rule = Open2NT()

    def test_20_hcp_balanced(self):
        """SAYC: 20-21 HCP balanced opens 2NT."""
        # AKQ3=9, KJ8=4, AQ3=6, J84=1 → 20 HCP, 4-3-3-3
        ctx = _ctx("AKQ3.KJ8.AQ3.J84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"
        assert result.rule_name == "opening.2nt"

    def test_21_hcp_balanced(self):
        """SAYC: 21 HCP balanced opens 2NT."""
        # AKQ3=9, KQ3=5, AJ8=5, Q84=2 → 21 HCP, 4-3-3-3
        ctx = _ctx("AKQ3.KQ3.AJ8.Q84")
        assert self.rule.applies(ctx)

    def test_19_hcp_too_low(self):
        """19 HCP does not qualify for 2NT."""
        # AKQ3=9, KJ8=4, A83=4, Q84=2 → 19 HCP, 4-3-3-3
        ctx = _ctx("AKQ3.KJ8.A83.Q84")
        assert not self.rule.applies(ctx)

    def test_22_hcp_too_high(self):
        """22+ HCP opens 2C, not 2NT."""
        # AKQ3=9, KQJ=6, AJ8=5, A84=4 → 24 HCP, 4-3-3-3
        ctx = _ctx("AKQ3.KQJ.AJ8.A84")
        assert not self.rule.applies(ctx)

    def test_20_hcp_unbalanced_rejected(self):
        """20 HCP but unbalanced shape doesn't qualify."""
        # AKQ32=9, AKJ8=8, AQ3=6, 4=0 → 23 HCP, 5-4-3-1 (not balanced)
        ctx = _ctx("AKQ32.AKJ8.AQ3.4")
        assert not self.rule.applies(ctx)
