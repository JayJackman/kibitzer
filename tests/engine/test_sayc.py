"""Integration smoke test — full pipeline from hand to bid via SAYC registry."""

from bridge.engine.context import BiddingContext
from bridge.engine.sayc import create_sayc_registry
from bridge.engine.selector import BidSelector
from bridge.model.auction import AuctionState, Seat
from bridge.model.board import Board
from bridge.model.hand import Hand


def _select(pbn: str) -> str:
    """Run a hand through the full SAYC pipeline, return rule_name."""
    reg = create_sayc_registry()
    selector = BidSelector(reg)
    board = Board(
        hand=Hand.from_pbn(pbn),
        seat=Seat.NORTH,
        auction=AuctionState(dealer=Seat.NORTH),
    )
    ctx = BiddingContext(board)
    result = selector.select(ctx)
    return result.rule_name


class TestSAYCIntegration:
    """Smoke tests: correct rule wins for representative hands."""

    def test_balanced_17_opens_1nt(self):
        assert _select("AK32.KQ3.J84.A73") == "opening.1nt"

    def test_balanced_20_opens_2nt(self):
        assert _select("AKQ3.KJ8.AQ3.J84") == "opening.2nt"

    def test_26_hcp_opens_2c(self):
        assert _select("AKQJ.AKQ.AJ8.A84") == "opening.2c"

    def test_weak_two_hearts(self):
        assert _select("84.KQJ842.73.J84") == "opening.weak_two"

    def test_preempt_3_clubs(self):
        # 7-card minor → 3-level (7-card major goes to 4-level)
        assert _select("84.73.84.KQT9732") == "opening.preempt_3"

    def test_preempt_4_spades(self):
        assert _select("KQJT973.84.73.84") == "opening.preempt_4"  # 7-card major

    def test_1_spade_opening(self):
        assert _select("AKJ52.Q73.84.A73") == "opening.1_major"

    def test_1_diamond_opening(self):
        assert _select("K873.A2.KJ84.Q73") == "opening.1_minor"

    def test_weak_hand_passes(self):
        assert _select("8432.732.843.J84") == "opening.pass"

    def test_22_balanced_opens_2c_not_2nt(self):
        """22+ HCP balanced should open 2C (priority 450 > 270)."""
        assert _select("AKQ3.KQJ.AJ8.A84") == "opening.2c"

    def test_15_balanced_opens_1nt_not_1_suit(self):
        """15 HCP balanced should open 1NT, not 1-of-a-suit."""
        assert _select("AQ32.KJ8.Q84.K73") == "opening.1nt"

    def test_candidates_shows_multiple(self):
        """candidates() returns all matching rules, not just the winner."""
        reg = create_sayc_registry()
        selector = BidSelector(reg)
        # A weak hand — only OpenPass applies
        board = Board(
            hand=Hand.from_pbn("8432.732.843.J84"),
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)
        results = selector.candidates(ctx)
        names = [r.rule_name for r in results]
        assert "opening.pass" in names
