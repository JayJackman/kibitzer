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


class TestSAYC1NTResponseIntegration:
    """Smoke tests: correct response to 1NT wins for representative hands."""

    def test_stayman_4_hearts(self):
        """4 hearts, 10+ HCP, non-flat -> Stayman."""
        # KJ43.AQ42.K43.42 = 12 HCP, 4-4-3-2
        assert _response_select("KJ43.AQ42.K43.42", "1NT") == "response.stayman"

    def test_jacoby_transfer_5_hearts(self):
        """5+ hearts -> Jacoby transfer 2D."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        assert _response_select("432.KJ432.43.432", "1NT") == "response.jacoby_transfer"

    def test_texas_transfer_6_hearts(self):
        """6+ hearts, 10-15 HCP -> Texas transfer 4D."""
        # K4.AQJ932.K43.42 = 13 HCP, 2-6-3-2
        assert _response_select("K4.AQJ932.K43.42", "1NT") == "response.texas_transfer"

    def test_3nt_over_1nt(self):
        """10-15 HCP, no conventions apply -> 3NT."""
        # KJ4.Q42.KJ3.Q432 = 11 HCP, 3-3-3-4
        assert _response_select("KJ4.Q42.KJ3.Q432", "1NT") == "response.3nt_over_1nt"

    def test_2nt_invite(self):
        """8-9 HCP, balanced -> 2NT invite."""
        # K43.QJ4.J43.Q432 = 9 HCP, 3-3-3-4
        assert _response_select("K43.QJ4.J43.Q432", "1NT") == "response.2nt_over_1nt"

    def test_2s_puppet_weak_minor(self):
        """0-7 HCP, 6+ minor -> 2S puppet."""
        # 432.43.43.QJ8432 = 3 HCP, 3-2-2-6
        assert _response_select("432.43.43.QJ8432", "1NT") == "response.2s_puppet"

    def test_pass_weak_flat(self):
        """0-7 HCP, no conventions -> pass."""
        # 432.J42.J43.5432 = 2 HCP, 3-3-3-4
        assert _response_select("432.J42.J43.5432", "1NT") == "response.pass_over_1nt"

    def test_gerber_18_hcp(self):
        """18+ HCP, balanced -> Gerber 4C."""
        # AKQ3.AJ4.KQ3.K42 = 22 HCP, 4-3-3-3
        assert _response_select("AKQ3.AJ4.KQ3.K42", "1NT") == "response.gerber"

    def test_garbage_stayman(self):
        """4-4 majors, weak -> garbage Stayman."""
        # J432.Q432.43.432 = 3 HCP, 4-4-2-3
        assert _response_select("J432.Q432.43.432", "1NT") == "response.stayman"


class TestSAYC1NTRebidIntegration:
    """Smoke tests: opener rebids correctly after 1NT opening."""

    def test_stayman_2h_with_4_hearts(self):
        """4+ hearts -> 2H after Stayman."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP, 3-4-3-3
        assert _rebid_select("AQ3.KJ42.QJ3.K43", "1NT", "2C") == "rebid.stayman_2h"

    def test_stayman_2d_no_major(self):
        """No 4-card major -> 2D denial."""
        # AQ3.KJ4.QJ3.K432 = 15 HCP, 3-3-3-4
        assert _rebid_select("AQ3.KJ4.QJ3.K432", "1NT", "2C") == "rebid.stayman_2d"

    def test_complete_transfer_2h(self):
        """Complete Jacoby transfer 2D -> 2H."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        assert (
            _rebid_select("AQ3.QJ4.KJ3.Q432", "1NT", "2D") == "rebid.complete_transfer"
        )

    def test_super_accept_17_hcp(self):
        """17 HCP, 4+ support -> super-accept."""
        # AK3.KQ42.QJ3.Q43 = 17 HCP, 3-4-3-3
        assert _rebid_select("AK3.KQ42.QJ3.Q43", "1NT", "2D") == "rebid.super_accept"

    def test_complete_2s_puppet(self):
        """2S puppet -> forced 3C."""
        assert (
            _rebid_select("AQ3.QJ4.KJ3.Q432", "1NT", "2S") == "rebid.complete_2s_puppet"
        )

    def test_gerber_response_2_aces(self):
        """2 aces -> 4S after Gerber."""
        # AQ3.KQ4.AJ3.Q432 = 17 HCP, 2 aces
        assert _rebid_select("AQ3.KQ4.AJ3.Q432", "1NT", "4C") == "rebid.gerber_response"

    def test_pass_after_3nt(self):
        """3NT is to play -> pass."""
        assert (
            _rebid_select("AQ3.KJ42.QJ3.K43", "1NT", "3NT")
            == "rebid.pass_after_3nt_over_1nt"
        )

    def test_accept_4nt_max(self):
        """16+ HCP -> accept quantitative 4NT, bid 6NT."""
        assert (
            _rebid_select("AQ3.KJ42.QJ3.K43", "1NT", "4NT")
            == "rebid.accept_4nt_over_1nt"
        )


class TestSAYC2NTResponseIntegration:
    """Smoke tests: correct response to 2NT wins for representative hands."""

    def test_stayman_4_hearts(self):
        """4 hearts, 5+ HCP, non-flat -> Stayman 3C."""
        # Q432.QJ42.43.432 = 4 HCP, 4-4-2-3
        assert _response_select("Q432.QJ42.43.432", "2NT") == "response.stayman_2nt"

    def test_transfer_5_hearts(self):
        """5+ hearts -> transfer 3D."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        assert _response_select("432.KJ432.43.432", "2NT") == "response.transfer_2nt"

    def test_texas_6_hearts(self):
        """6+ hearts, 4-10 HCP -> Texas 4D."""
        # 43.KQJ932.Q43.42 = 8 HCP, 2-6-3-2
        assert _response_select("43.KQJ932.Q43.42", "2NT") == "response.texas_2nt"

    def test_3nt_over_2nt(self):
        """4-10 HCP, no conventions apply -> 3NT."""
        # Q43.J42.K43.J432 = 7 HCP, 3-3-3-4
        assert _response_select("Q43.J42.K43.J432", "2NT") == "response.3nt_over_2nt"

    def test_gerber_13_hcp(self):
        """13+ HCP, balanced -> Gerber 4C."""
        # AQ3.KJ4.KQ3.Q432 = 16 HCP, 3-3-3-4
        assert _response_select("AQ3.KJ4.KQ3.Q432", "2NT") == "response.gerber_2nt"

    def test_4nt_quantitative(self):
        """11-12 HCP, balanced -> quantitative 4NT."""
        # AQ3.K42.J43.Q432 = 12 HCP, 3-3-3-4
        assert _response_select("AQ3.K42.J43.Q432", "2NT") == "response.4nt_over_2nt"

    def test_3s_puppet_weak_minor(self):
        """0-3 HCP, 6+ minor -> 3S puppet."""
        # 432.43.43.J98432 = 1 HCP, 3-2-2-6
        assert _response_select("432.43.43.J98432", "2NT") == "response.3s_puppet_2nt"

    def test_pass_weak_flat(self):
        """0-3 HCP, no conventions -> pass."""
        # 432.J42.432.5432 = 1 HCP, 3-3-3-4
        assert _response_select("432.J42.432.5432", "2NT") == "response.pass_over_2nt"


class TestSAYC2NTRebidIntegration:
    """Smoke tests: opener rebids correctly after 2NT opening."""

    def test_stayman_3h_with_4_hearts(self):
        """4+ hearts -> 3H after Stayman."""
        # AQ3.KQ42.AQ3.K43 = 20 HCP, 3-4-3-3
        assert _rebid_select("AQ3.KQ42.AQ3.K43", "2NT", "3C") == "rebid.stayman_3h_2nt"

    def test_stayman_3d_no_major(self):
        """No 4-card major -> 3D denial."""
        # AQ3.KQ4.AQ32.K43 = 20 HCP, 3-3-4-3
        assert _rebid_select("AQ3.KQ4.AQ32.K43", "2NT", "3C") == "rebid.stayman_3d_2nt"

    def test_complete_transfer_3h(self):
        """Complete transfer 3D -> 3H."""
        assert (
            _rebid_select("AQ3.KQ4.AQ32.K43", "2NT", "3D")
            == "rebid.complete_transfer_2nt"
        )

    def test_complete_3s_puppet(self):
        """3S puppet -> forced 4C."""
        assert (
            _rebid_select("AQ3.KQ4.AQ32.K43", "2NT", "3S")
            == "rebid.complete_3s_puppet_2nt"
        )

    def test_gerber_response_2_aces(self):
        """2 aces -> 4S after Gerber."""
        # AQ3.AQ4.KQ32.K43 = 21 HCP, 2 aces
        assert (
            _rebid_select("AQ3.AQ4.KQ32.K43", "2NT", "4C")
            == "rebid.gerber_response_2nt"
        )

    def test_complete_texas_4d(self):
        """4D -> 4H (Texas complete)."""
        assert (
            _rebid_select("AQ3.KQ4.AQ32.K43", "2NT", "4D") == "rebid.complete_texas_2nt"
        )

    def test_pass_after_3nt(self):
        """3NT is to play -> pass."""
        assert (
            _rebid_select("AQ3.KQ42.AQ3.K43", "2NT", "3NT")
            == "rebid.pass_after_3nt_over_2nt"
        )

    def test_accept_4nt_21_hcp(self):
        """21 HCP -> accept 4NT, bid 6NT."""
        assert (
            _rebid_select("AQ3.AQ4.AQ32.K43", "2NT", "4NT")
            == "rebid.accept_4nt_over_2nt"
        )

    def test_decline_4nt_20_hcp(self):
        """20 HCP -> decline 4NT, pass."""
        assert (
            _rebid_select("AQ3.KQ4.AQ32.K43", "2NT", "4NT")
            == "rebid.decline_4nt_over_2nt"
        )


# ── 2C Response Integration ──────────────────────────────────────────────


class TestSAYC2CResponseIntegration:
    """Smoke tests: correct response rule wins after 2C opening."""

    def test_2nt_positive_balanced(self):
        """9 HCP, balanced -> 2NT positive."""
        # KJ3.Q42.K43.5432 = K=3+J=1+Q=2+K=3 = 9 HCP, balanced
        assert _response_select("KJ3.Q42.K43.5432", "2C") == "response.2nt_over_2c"

    def test_positive_suit_hearts(self):
        """10 HCP, 5 hearts with AK -> 2H positive."""
        # 5432.AK432.K4.32 = A=4+K=3+K=3 = 10 HCP, 5H with AK
        assert _response_select("5432.AK432.K4.32", "2C") == "response.positive_suit_2c"

    def test_positive_suit_spades(self):
        """9 HCP, 5 spades with AQ, unbalanced -> 2S positive."""
        # AQ432.K43.2.5432 = A=4+Q=2+K=3 = 9 HCP, 5-3-1-4 unbalanced
        assert _response_select("AQ432.K43.2.5432", "2C") == "response.positive_suit_2c"

    def test_2d_waiting_weak(self):
        """0 HCP -> 2D waiting."""
        assert _response_select("5432.5432.5432.5", "2C") == "response.2d_waiting"

    def test_2d_waiting_no_quality_suit(self):
        """8 HCP, unbalanced, no quality suit -> 2D waiting."""
        # AJ432.K43.2.Q432 = A=4+J=1+K=3+Q=2 = 10 HCP, 5-3-1-4 unbalanced
        # Only A in spades (1 of top 3), not balanced -> 2D
        assert _response_select("AJ432.K43.2.Q432", "2C") == "response.2d_waiting"

    def test_balanced_prefers_2nt_over_positive_suit(self):
        """11 HCP, balanced, 5 AQ spades -> 2NT (not positive suit)."""
        # AQ432.K43.Q43.32 = A=4+Q=2+K=3+Q=2 = 11 HCP, balanced 5-3-3-2
        assert _response_select("AQ432.K43.Q43.32", "2C") == "response.2nt_over_2c"


# ── 2C Rebid Integration ─────────────────────────────────────────────────


class TestSAYC2CRebidIntegration:
    """Smoke tests: correct rebid rule wins after 2C opening."""

    def test_2nt_after_2d(self):
        """22 HCP, balanced, after 2D -> 2NT."""
        # AKQ3.AJ4.KQ3.K43 = 22 HCP, balanced
        assert _rebid_select("AKQ3.AJ4.KQ3.K43", "2C", "2D") == "rebid.2nt_after_2c"

    def test_3nt_after_2d(self):
        """25 HCP, balanced, after 2D -> 3NT."""
        # AKQ3.AQ4.AK3.K43 = 25 HCP, balanced
        assert _rebid_select("AKQ3.AQ4.AK3.K43", "2C", "2D") == "rebid.3nt_after_2c"

    def test_suit_after_2d(self):
        """6 hearts, unbalanced, after 2D -> 2H."""
        # AK2.AKQ432.A.432 = A=4+K=3+A=4+K=3+Q=2+A=4 = 20 HCP, 6H
        assert _rebid_select("AK2.AKQ432.A.432", "2C", "2D") == "rebid.suit_after_2c"

    def test_raise_after_positive(self):
        """4+ hearts after partner's 2H -> raise to 3H."""
        # AK32.AK43.AK.432 = 21 HCP, 4 hearts
        assert (
            _rebid_select("AK32.AK43.AK.432", "2C", "2H")
            == "rebid.raise_after_positive_2c"
        )

    def test_suit_after_positive(self):
        """5+ spades after partner's 2H, <4 hearts -> 2S."""
        # AKQJ2.A32.AK.432 = 21 HCP, 5 spades, 3 hearts
        assert (
            _rebid_select("AKQJ2.A32.AK.432", "2C", "2H")
            == "rebid.suit_after_positive_2c"
        )

    def test_3nt_after_positive(self):
        """No fit, no 5+ suit after positive -> 3NT."""
        # AK32.A32.AK3.K32 = 21 HCP, 4-3-3-3
        assert (
            _rebid_select("AK32.A32.AK3.K32", "2C", "2H")
            == "rebid.nt_after_positive_2c"
        )

    def test_suit_after_2nt_positive(self):
        """5+ spades after partner's 2NT -> 3S."""
        # AKQJ2.AK3.AK.432 = 24 HCP, 5 spades
        assert (
            _rebid_select("AKQJ2.AK3.AK.432", "2C", "2NT")
            == "rebid.suit_after_positive_2c"
        )

    def test_3nt_after_2nt_positive(self):
        """Balanced, no 5+ suit after partner's 2NT -> 3NT."""
        assert (
            _rebid_select("AK32.A32.AK3.K32", "2C", "2NT")
            == "rebid.nt_after_positive_2c"
        )
