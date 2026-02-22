"""Integration smoke test — full pipeline from hand to bid via SAYC registry."""

from bridge.engine.context import BiddingContext
from bridge.engine.sayc import create_sayc_registry
from bridge.engine.selector import BidSelector
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, parse_bid
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


def _response_select(pbn: str, opening: str = "1H") -> str:
    """Run a hand through the full SAYC pipeline as responder, return rule_name.

    North opens, East passes, South (responder) acts.
    """
    reg = create_sayc_registry()
    selector = BidSelector(reg)
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    board = Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
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
        # 13 HCP, 5 spades — matches Open1Major *and* OpenPass
        board = Board(
            hand=Hand.from_pbn("AKJ52.Q73.84.A73"),
            seat=Seat.NORTH,
            auction=AuctionState(dealer=Seat.NORTH),
        )
        ctx = BiddingContext(board)
        results = selector.candidates(ctx)
        names = [r.rule_name for r in results]
        assert len(results) >= 2
        assert "opening.1_major" in names
        assert "opening.pass" in names


class TestSAYCResponseIntegration:
    """Smoke tests: correct response rule wins for representative hands."""

    # ── Responses to 1H ────────────────────────────────────────────

    def test_jump_shift_over_1h(self):
        """19+ HCP, 5-card spade suit → jump shift."""
        assert _response_select("AKQ93.84.AKJ3.A4", "1H") == "response.jump_shift"

    def test_jacoby_2nt_over_1h(self):
        """4+ heart support, 13+ support pts → Jacoby 2NT."""
        assert _response_select("K842.AJ83.A4.K73", "1H") == "response.jacoby_2nt"

    def test_game_raise_over_1h(self):
        """5+ support, singleton, <10 HCP → preemptive 4H."""
        assert _response_select("84.KJ842.4.98743", "1H") == "response.game_raise_major"

    def test_3nt_over_1h(self):
        """15-17 balanced, exactly 2-card support → 3NT."""
        assert _response_select("AQ32.84.KQ84.AJ3", "1H") == "response.3nt_over_major"

    def test_limit_raise_over_1h(self):
        """3+ support, 10-12 support pts → limit raise 3H."""
        assert (
            _response_select("K84.QJ3.A842.973", "1H") == "response.limit_raise_major"
        )

    def test_2_over_1_over_1h(self):
        """10+ HCP, 5-card diamond suit → 2D."""
        assert _response_select("84.73.AKJ84.K973", "1H") == "response.2_over_1"

    def test_new_suit_1s_over_1h(self):
        """4+ spades, 6-9 HCP → 1S over 1H."""
        # KJ84=4, 73=0, Q84=2, 9732=0 → 6 HCP, 4-2-3-4
        assert _response_select("KJ84.73.Q84.9732", "1H") == "response.new_suit_1_level"

    def test_single_raise_over_1h(self):
        """3+ support, 6-10 support pts → 2H."""
        assert (
            _response_select("K84.QJ3.843.9732", "1H") == "response.single_raise_major"
        )

    def test_1nt_over_1h(self):
        """6-10 HCP, <3 support, no 4 spades → 1NT."""
        assert _response_select("K84.73.QJ84.9732", "1H") == "response.1nt_over_major"

    def test_pass_over_1h(self):
        """<6 HCP → pass."""
        assert _response_select("843.73.J842.9732", "1H") == "response.pass"

    # ── Responses to 1S ────────────────────────────────────────────

    def test_jacoby_2nt_over_1s(self):
        """4+ spade support, 13+ support pts → Jacoby 2NT."""
        assert _response_select("AJ83.K842.A4.K73", "1S") == "response.jacoby_2nt"

    def test_limit_raise_over_1s(self):
        """3+ support, 10-12 support pts → 3S."""
        assert (
            _response_select("K843.73.QJ3.A842", "1S") == "response.limit_raise_major"
        )

    def test_2_over_1_over_1s(self):
        """10+ HCP, 5-card diamond suit → 2D over 1S."""
        assert _response_select("QJ3.84.AKJ84.K97", "1S") == "response.2_over_1"

    # ── Responses to 1D ────────────────────────────────────────────

    def test_new_suit_1h_over_1d(self):
        """4-card major up the line over 1D, 6-9 HCP."""
        # 843=0, KQ73=5, 84=0, J973=1 → 6 HCP, 3-4-2-4
        assert _response_select("843.KQ73.84.J973", "1D") == "response.new_suit_1_level"

    def test_new_suit_1h_over_1d_with_10_hcp(self):
        """10+ HCP with 4 hearts over 1D → 1H (not 2H)."""
        # K84=3, AQ73=6, 84=0, J73=1 → 10 HCP, 3-4-2-3
        assert _response_select("K84.AQ73.84.J973", "1D") == "response.new_suit_1_level"

    def test_single_raise_2d(self):
        """4+ diamonds, 6-10 HCP, no major → 2D."""
        assert (
            _response_select("K84.Q73.QJ84.973", "1D") == "response.single_raise_minor"
        )

    def test_2nt_over_1d(self):
        """13-15 balanced, no major → 2NT."""
        assert _response_select("AQ3.K84.KJ84.973", "1D") == "response.2nt_over_minor"

    def test_pass_over_1d(self):
        """<6 HCP → pass."""
        assert _response_select("843.973.J842.973", "1D") == "response.pass"

    # ── Responses to 1C ────────────────────────────────────────────

    def test_new_suit_1h_over_1c(self):
        """4-card major up the line over 1C, 6-9 HCP."""
        # 843=0, KQ73=5, J84=1, 973=0 → 6 HCP, 3-4-3-3
        assert _response_select("843.KQ73.J84.973", "1C") == "response.new_suit_1_level"

    def test_1nt_over_1c(self):
        """6-10 HCP, no major, <5 clubs → 1NT."""
        assert _response_select("K84.Q73.973.QJ84", "1C") == "response.1nt_over_minor"

    def test_single_raise_2c(self):
        """5+ clubs, 6-10 HCP → 2C."""
        assert (
            _response_select("K84.Q73.73.QJ984", "1C") == "response.single_raise_minor"
        )

    def test_pass_over_1c(self):
        """<6 HCP → pass."""
        assert _response_select("843.973.973.J842", "1C") == "response.pass"


def _rebid_select(pbn: str, opening: str, response: str) -> str:
    """Run a hand through the full SAYC pipeline as opener rebidding.

    North opens, East passes, South responds, West passes, North rebids.
    """
    reg = create_sayc_registry()
    selector = BidSelector(reg)
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    auction.add_bid(parse_bid(response))
    auction.add_bid(PASS)
    board = Board(hand=Hand.from_pbn(pbn), seat=Seat.NORTH, auction=auction)
    ctx = BiddingContext(board)
    result = selector.select(ctx)
    return result.rule_name


class TestSAYCRebidIntegration:
    """Smoke tests: correct rebid rule wins for representative hands."""

    # ── After single raise of major ─────────────────────────────────

    def test_game_after_raise_19_bergen(self):
        """19+ Bergen pts → 4S after 1S→2S."""
        assert (
            _rebid_select("AKJ52.A3.K84.A73", "1S", "2S")
            == "rebid.game_after_raise_major"
        )

    def test_invite_after_raise_17_bergen(self):
        """17 Bergen pts → 3S (invite) after 1S→2S."""
        assert (
            _rebid_select("AKJ52.KQ3.84.A73", "1S", "2S")
            == "rebid.invite_after_raise_major"
        )

    def test_pass_after_raise_minimum(self):
        """13 Bergen pts → pass after 1S→2S."""
        assert _rebid_select("KJ852.KQ3.84.A73", "1S", "2S") == "rebid.pass_after_raise"

    # ── After limit raise of major ──────────────────────────────────

    def test_accept_limit_raise(self):
        """17 Bergen pts → 4S after 1S→3S."""
        assert (
            _rebid_select("AKJ52.KQ3.84.A73", "1S", "3S")
            == "rebid.accept_limit_raise_major"
        )

    def test_decline_limit_raise(self):
        """11 Bergen pts → pass after 1S→3S."""
        assert (
            _rebid_select("KJ852.Q73.84.A73", "1S", "3S") == "rebid.decline_limit_raise"
        )

    # ── After 1NT response ──────────────────────────────────────────

    def test_2nt_over_1nt_18_balanced(self):
        """18 HCP balanced → 2NT over 1NT."""
        # AKJ3=8, KQ8=5, Q84=2, K73=3 → 18 HCP, 4-3-3-3
        assert _rebid_select("AKJ3.KQ8.Q84.K73", "1S", "1NT") == "rebid.2nt_over_1nt"

    def test_rebid_suit_over_1nt(self):
        """6-card suit, minimum → 2S over 1NT."""
        assert (
            _rebid_select("KJ8532.KQ3.8.A73", "1S", "1NT")
            == "rebid.rebid_suit_over_1nt"
        )

    def test_pass_over_1nt_balanced_min(self):
        """Balanced minimum with 5-card suit → pass over 1NT."""
        # KJ852.Q73.K4.A73 — 13 HCP, 5-3-2-3
        assert _rebid_select("KJ852.Q73.K4.A73", "1S", "1NT") == "rebid.pass_over_1nt"

    # ── After new suit at 1-level ───────────────────────────────────

    def test_raise_responder_4_card(self):
        """4-card support, minimum → 2S after 1H→1S."""
        assert _rebid_select("K842.AKJ52.Q7.73", "1H", "1S") == "rebid.raise_responder"

    def test_1nt_rebid_balanced(self):
        """12-14 HCP balanced → 1NT after 1H→1S."""
        assert _rebid_select("K73.AJ852.Q73.Q7", "1H", "1S") == "rebid.1nt"

    def test_reverse_17_pts(self):
        """17+ pts, higher suit → reverse after 1D→1S."""
        # 8=0, AQ73=6, AKJ52=8, Q73=2 → 16 HCP + 1 len = 17 total, 1-4-5-3
        assert _rebid_select("8.AQ73.AKJ52.Q73", "1D", "1S") == "rebid.reverse"

    # ── After 2-over-1 ──────────────────────────────────────────────

    def test_rebid_suit_after_2over1(self):
        """6+ card suit → rebid after 2-over-1."""
        assert (
            _rebid_select("A4.AKJ852.Q7.K73", "1H", "2C")
            == "rebid.rebid_suit_after_2over1"
        )

    def test_new_suit_after_2over1(self):
        """Third suit after 2-over-1."""
        assert (
            _rebid_select("AK42.AKJ52.Q7.73", "1H", "2C")
            == "rebid.new_suit_after_2over1"
        )
