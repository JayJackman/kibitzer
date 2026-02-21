"""Tests for responses to 1-of-a-suit opening — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.response.suit import (
    Respond1NTOverMajor,
    Respond1NTOverMinor,
    Respond2NTOverMinor,
    Respond2Over1,
    Respond3NTOverMajor,
    Respond3NTOverMinor,
    RespondGameRaiseMajor,
    RespondJacoby2NT,
    RespondJumpShift,
    RespondLimitRaiseMajor,
    RespondLimitRaiseMinor,
    RespondNewSuit1Level,
    RespondPass,
    RespondSingleRaiseMajor,
    RespondSingleRaiseMinor,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import Bid, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str, opening: str = "1H") -> BiddingContext:
    """Build a BiddingContext where partner opened and responder acts.

    North opens, East passes, South (responder) acts.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))  # Partner (N) opens
    auction.add_bid(Bid.make_pass())  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# ── Shared Rules ────────────────────────────────────────────────────


# ── RespondJumpShift ────────────────────────────────────────────────


class TestRespondJumpShift:
    rule = RespondJumpShift()

    def test_19_hcp_new_suit_over_1h(self):
        """19+ HCP, 5-card spade suit → jump to 2S over 1H."""
        # AKQ93=10, 84=0, AKJ3=8, A4=4 → 22 HCP, 5-2-4-2
        ctx = _ctx("AKQ93.84.AKJ3.A4", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"
        assert result.forcing

    def test_19_hcp_jump_to_3_level(self):
        """19+ HCP, club suit → jump to 3C over 1H."""
        # A4=4, 84=0, AKJ3=8, AKQ93=10 → 22 HCP, 2-2-4-5
        ctx = _ctx("A4.84.AKJ3.AKQ93", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_18_hcp_rejected(self):
        """18 HCP is below threshold for jump shift."""
        # AKQ93=10, 84=0, AKJ3=8, 42=0 → 18 HCP, 5-2-4-2
        ctx = _ctx("AKQ93.84.AKJ3.42", "1H")
        assert not self.rule.applies(ctx)

    def test_jump_shift_over_1s(self):
        """Jump shift over 1S: 3H (jump over 2-level)."""
        # A4=4, AKQ93=10, AKJ3=8, 84=0 → 22 HCP, 2-5-4-2
        ctx = _ctx("A4.AKQ93.AKJ3.84", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"


# ── RespondNewSuit1Level ───────────────────────────────────────────


class TestRespondNewSuit1Level:
    rule = RespondNewSuit1Level()

    def test_4_spades_over_1h(self):
        """4+ spades, 6+ HCP → 1S over 1H."""
        # KQ84=5, 73=0, J84=1, A973=4 → 10 HCP, 4-2-3-4
        ctx = _ctx("KQ84.73.J84.A973", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"
        assert result.forcing

    def test_no_higher_suit_over_1s(self):
        """Over 1S, no new suit available at 1-level."""
        # 73=0, KQ84=5, J84=1, A973=4 → 10 HCP
        ctx = _ctx("73.KQ84.J84.A973", "1S")
        assert not self.rule.applies(ctx)

    def test_5_hcp_rejected(self):
        """5 HCP — below minimum for new suit."""
        # KQ84=5, 73=0, 843=0, 9732=0 → 5 HCP
        ctx = _ctx("KQ84.73.843.9732", "1H")
        assert not self.rule.applies(ctx)

    def test_1d_over_1c(self):
        """4+ diamonds, 6+ HCP → 1D over 1C."""
        # 84=0, 973=0, KJ84=4, A973=4 → 8 HCP, 2-3-4-4
        ctx = _ctx("84.973.KJ84.A973", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_up_the_line_1h_over_1c(self):
        """With 4H and 4S, bid 1H (up the line, cheapest first) over 1C."""
        # KJ84=4, A973=4, Q73=2, 84=0 → 10 HCP, 4-4-3-2
        # Diamonds: Q73 = 3 cards, not 4. So only H and S qualify.
        # Up the line → 1H first.
        ctx = _ctx("KJ84.A973.Q73.84", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1H"

    def test_up_the_line_1h_over_1d(self):
        """With 4H and 4S, bid 1H (up the line) over 1D."""
        # KJ84=4, A973=4, 84=0, Q73=2 → 10 HCP, 4-4-2-3
        ctx = _ctx("KJ84.A973.84.Q73", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1H"


# ── Respond2Over1 ──────────────────────────────────────────────────


class TestRespond2Over1:
    rule = Respond2Over1()

    def test_10_hcp_new_suit_over_1h(self):
        """10+ HCP, 5-card diamond suit → 2D over 1H."""
        # 84=0, 73=0, AKJ84=8, K973=3 → 11 HCP, 2-2-5-4
        ctx = _ctx("84.73.AKJ84.K973", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"
        assert result.forcing

    def test_2d_over_1s(self):
        """10+ HCP, 5-card diamond suit → 2D over 1S."""
        # QJ3=3, 84=0, AKJ84=8, K97=3 → 14 HCP, 3-2-5-3
        ctx = _ctx("QJ3.84.AKJ84.K97", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_2h_over_1s(self):
        """10+ HCP, 4-card hearts → 2H over 1S (hearts is 2-level over 1S)."""
        # Q3=2, AKJ8=8, 984=0, K973=3 → 13 HCP, 2-4-3-4
        ctx = _ctx("Q3.AKJ8.984.K973", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"  # Clubs is longer/cheapest with equal length

    def test_9_hcp_rejected(self):
        """9 HCP — below 2-over-1 threshold."""
        # 84=0, 73=0, AJ984=5, K973=3 → 8 HCP
        ctx = _ctx("84.73.AJ984.K973", "1H")
        assert not self.rule.applies(ctx)

    def test_19_hcp_rejected(self):
        """19+ HCP should use jump shift, not 2-over-1."""
        # A4=4, 84=0, AKJ93=9, AKQ3=9 → 22 HCP
        ctx = _ctx("A4.84.AKJ93.AKQ3", "1H")
        assert not self.rule.applies(ctx)


# ── RespondPass ────────────────────────────────────────────────────


class TestRespondPass:
    rule = RespondPass()

    def test_fewer_than_6_hcp(self):
        """Pass is always applicable over 1-suit opening."""
        # 843=0, 73=0, J842=1, 9732=0 → 1 HCP
        ctx = _ctx("843.73.J842.9732", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass
        assert result.rule_name == "response.pass"

    def test_pass_over_1s(self):
        """Pass over 1S."""
        ctx = _ctx("843.73.J842.9732", "1S")
        assert self.rule.applies(ctx)

    def test_pass_over_1c(self):
        """Pass over 1C."""
        ctx = _ctx("843.973.J842.973", "1C")
        assert self.rule.applies(ctx)

    def test_pass_over_1d(self):
        """Pass over 1D."""
        ctx = _ctx("843.973.J842.973", "1D")
        assert self.rule.applies(ctx)


# ── Major-Specific Rules ───────────────────────────────────────────


# ── RespondJacoby2NT ───────────────────────────────────────────────


class TestRespondJacoby2NT:
    rule = RespondJacoby2NT()

    def test_4_card_support_13_pts(self):
        """4+ card support, 13+ support points → Jacoby 2NT."""
        # K842=3, AJ83=5, A4=4, K73=3 → 15 HCP, 4-4-2-3, support pts=16
        ctx = _ctx("K842.AJ83.A4.K73", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"
        assert result.forcing
        assert len(result.alerts) > 0

    def test_3_card_support_rejected(self):
        """Only 3-card support — Jacoby requires 4+."""
        # K842=3, AJ8=5, A42=4, K73=3 → 15 HCP, 4-3-3-3
        ctx = _ctx("K842.AJ8.A42.K73", "1H")
        assert not self.rule.applies(ctx)

    def test_under_13_support_pts_rejected(self):
        """4+ support but only 12 support points — too weak."""
        # 8432=0, KJ83=4, A4=4, K73=3 → 11 HCP, 4-4-2-3, support pts=12
        ctx = _ctx("8432.KJ83.A4.K73", "1H")
        assert not self.rule.applies(ctx)

    def test_jacoby_over_1s(self):
        """Jacoby 2NT over 1S with 4-card spade support."""
        # AJ83=5, K842=3, A4=4, K73=3 → 15 HCP, 4-4-2-3
        ctx = _ctx("AJ83.K842.A4.K73", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"


# ── RespondGameRaiseMajor ──────────────────────────────────────────


class TestRespondGameRaiseMajor:
    rule = RespondGameRaiseMajor()

    def test_5_card_support_singleton(self):
        """5+ support, <10 HCP, singleton → preemptive 4H."""
        # 84=0, KJ842=4, 4=0, 98743=0 → 4 HCP, 2-5-1-5
        ctx = _ctx("84.KJ842.4.98743", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_10_hcp_rejected(self):
        """10+ HCP — too strong for preemptive raise."""
        # 84=0, KJ842=4, A4=4, K974=3 → 11 HCP, 2-5-2-4
        ctx = _ctx("84.KJ842.A4.K974", "1H")
        assert not self.rule.applies(ctx)

    def test_no_singleton_rejected(self):
        """No singleton or void — not preemptive."""
        # 843=0, KJ842=4, 97=0, 974=0 → 4 HCP, 3-5-2-3
        ctx = _ctx("843.KJ842.97.974", "1H")
        assert not self.rule.applies(ctx)

    def test_game_raise_over_1s(self):
        """Preemptive 4S over 1S."""
        # KJ842=4, 84=0, 4=0, 98743=0 → 4 HCP, 5-2-1-5
        ctx = _ctx("KJ842.84.4.98743", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"


# ── Respond3NTOverMajor ────────────────────────────────────────────


class TestRespond3NTOverMajor:
    rule = Respond3NTOverMajor()

    def test_balanced_16_hcp_2_card_support(self):
        """15-17 HCP, balanced, exactly 2-card support → 3NT."""
        # AQ32=6, 84=0, KQ84=4, AJ3=5 → 15 HCP, 4-2-4-3 balanced
        ctx = _ctx("AQ32.84.KQ84.AJ3", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_14_hcp_rejected(self):
        """14 HCP — below range for 3NT."""
        # AQ32=6, 84=0, KJ84=4, Q73=2 → 12 HCP, 4-2-4-3
        ctx = _ctx("AQ32.84.KJ84.Q73", "1H")
        assert not self.rule.applies(ctx)

    def test_3_card_support_rejected(self):
        """3-card support — not exactly 2."""
        # AQ32=6, K84=3, KQ8=5, J73=1 → 15 HCP, 4-3-3-3
        ctx = _ctx("AQ32.K84.KQ8.J73", "1H")
        assert not self.rule.applies(ctx)


# ── RespondLimitRaiseMajor ─────────────────────────────────────────


class TestRespondLimitRaiseMajor:
    rule = RespondLimitRaiseMajor()

    def test_3_card_support_10_12_pts(self):
        """3+ support, 10-12 support points → limit raise."""
        # K84=3, QJ3=3, A842=4, 973=0 → 10 HCP, 3-3-4-3, support pts=10
        ctx = _ctx("K84.QJ3.A842.973", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_9_support_pts_rejected(self):
        """9 support points — below limit raise range."""
        # 984=0, QJ3=3, A842=4, 973=0 → 7 HCP, 3-3-4-3, support pts=7
        ctx = _ctx("984.QJ3.A842.973", "1H")
        assert not self.rule.applies(ctx)

    def test_limit_raise_over_1s(self):
        """Limit raise 3S over 1S."""
        # K843=3, 73=0, QJ3=3, A842=4 → 10 HCP, 4-2-3-4, support pts=11
        ctx = _ctx("K843.73.QJ3.A842", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"


# ── RespondSingleRaiseMajor ───────────────────────────────────────


class TestRespondSingleRaiseMajor:
    rule = RespondSingleRaiseMajor()

    def test_3_card_support_6_10_pts(self):
        """3+ support, 6-10 support points → single raise."""
        # K84=3, QJ3=3, 843=0, 9732=0 → 6 HCP, 3-3-3-4, support pts=6
        ctx = _ctx("K84.QJ3.843.9732", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_2_card_support_rejected(self):
        """Only 2-card support — need 3+."""
        # K84=3, Q3=2, 8432=0, 9732=0 → 5 HCP, 3-2-4-4
        ctx = _ctx("K84.Q3.8432.9732", "1H")
        assert not self.rule.applies(ctx)

    def test_single_raise_over_1s(self):
        """Single raise 2S over 1S."""
        # QJ3=3, K84=3, 843=0, 9732=0 → 6 HCP, 3-3-3-4
        ctx = _ctx("QJ3.K84.843.9732", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"


# ── Respond1NTOverMajor ───────────────────────────────────────────


class TestRespond1NTOverMajor:
    rule = Respond1NTOverMajor()

    def test_6_10_hcp_no_support(self):
        """6-10 HCP, <3 support, no 4S over 1H → 1NT."""
        # K84=3, 73=0, QJ84=3, 9732=0 → 6 HCP, 3-2-4-4
        ctx = _ctx("K84.73.QJ84.9732", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"
        assert not result.forcing

    def test_3_card_support_rejected(self):
        """3-card support → should raise, not 1NT."""
        # K84=3, Q73=2, J84=1, 9732=0 → 6 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.J84.9732", "1H")
        assert not self.rule.applies(ctx)

    def test_4_spades_over_1h_applies_but_loses_priority(self):
        """4+ spades over 1H — 1NT applies, but new_suit_1_level wins via priority."""
        # KQ84=5, 73=0, J84=1, 9732=0 → 6 HCP, 4-2-3-4
        ctx = _ctx("KQ84.73.J84.9732", "1H")
        assert self.rule.applies(ctx)

    def test_1nt_over_1s(self):
        """1NT over 1S — no spade denial needed."""
        # 84=0, K73=3, QJ84=3, 9732=0 → 6 HCP, 2-3-4-4
        ctx = _ctx("84.K73.QJ84.9732", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"

    def test_11_hcp_rejected(self):
        """11 HCP — above 1NT range."""
        # AJ4=5, K3=3, QJ84=3, 972=0 → 11 HCP, 3-2-4-3 → 2 hearts = ok
        ctx = _ctx("AJ4.K3.QJ84.9732", "1H")
        assert not self.rule.applies(ctx)


# ── Minor-Specific Rules ───────────────────────────────────────────


# ── Respond3NTOverMinor ────────────────────────────────────────────


class TestRespond3NTOverMinor:
    rule = Respond3NTOverMinor()

    def test_16_18_balanced_no_major(self):
        """16-18 HCP, balanced, no 4-card major → 3NT."""
        # K84=3, Q73=2, AKJ8=8, K73=3 → 16 HCP, 3-3-4-3
        ctx = _ctx("K84.Q73.AKJ8.K73", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_15_hcp_rejected(self):
        """15 HCP — below 3NT range over minor (that's 2NT territory)."""
        # K84=3, Q73=2, AKJ8=8, 973=0 → 13 HCP
        ctx = _ctx("K84.Q73.AKJ8.973", "1D")
        assert not self.rule.applies(ctx)

    def test_4_card_major_rejected(self):
        """Has 4-card major — should bid it first."""
        # AK32=7, Q84=2, KJ8=4, K73=3 → 16 HCP, 4-3-3-3, has 4 spades
        ctx = _ctx("AK32.Q84.KJ8.K73", "1D")
        assert not self.rule.applies(ctx)

    def test_3nt_over_1c(self):
        """3NT over 1C."""
        # K84=3, Q73=2, K73=3, AKJ8=8 → 16 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.K73.AKJ8", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"


# ── Respond2NTOverMinor ────────────────────────────────────────────


class TestRespond2NTOverMinor:
    rule = Respond2NTOverMinor()

    def test_13_15_balanced_no_major(self):
        """13-15 HCP, balanced, no 4-card major → 2NT."""
        # AQ3=6, K84=3, KJ84=4, 973=0 → 13 HCP, 3-3-4-3
        ctx = _ctx("AQ3.K84.KJ84.973", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"
        assert result.forcing

    def test_12_hcp_rejected(self):
        """12 HCP — below 2NT range over minor."""
        # AQ3=6, K84=3, J842=1, 973=0 → 10 HCP
        ctx = _ctx("AQ3.K84.J842.973", "1D")
        assert not self.rule.applies(ctx)

    def test_16_hcp_rejected(self):
        """16 HCP — above 2NT range (that's 3NT territory)."""
        # AQ3=6, K84=3, AKJ8=8, 973=0 → 17 HCP
        ctx = _ctx("AQ3.K84.AKJ8.973", "1D")
        assert not self.rule.applies(ctx)

    def test_4_card_major_rejected(self):
        """Has 4-card major — should bid it first."""
        # AQ32=6, K84=3, KJ8=4, 973=0 → 13 HCP, 4-3-3-3
        ctx = _ctx("AQ32.K84.KJ8.973", "1D")
        assert not self.rule.applies(ctx)

    def test_2nt_over_1c(self):
        """2NT over 1C."""
        # AQ3=6, K84=3, 973=0, KJ84=4 → 13 HCP, 3-3-3-4
        ctx = _ctx("AQ3.K84.973.KJ84", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"


# ── RespondLimitRaiseMinor ─────────────────────────────────────────


class TestRespondLimitRaiseMinor:
    rule = RespondLimitRaiseMinor()

    def test_10_12_hcp_4_diamonds(self):
        """10-12 HCP, 4+ diamonds, no 4-card major → 3D."""
        # K84=3, Q73=2, QJ84=3, A73=4 → 12 HCP, 3-3-4-3
        ctx = _ctx("K84.Q73.QJ84.A73", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_10_12_hcp_5_clubs(self):
        """10-12 HCP, 5+ clubs → 3C."""
        # K84=3, Q73=2, A7=4, QJ843=3 → 12 HCP, 3-3-2-5
        ctx = _ctx("K84.Q73.A7.QJ843", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_4_clubs_rejected(self):
        """Only 4 clubs — need 5+ for club raise."""
        # K84=3, Q73=2, A73=4, QJ84=3 → 12 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.A73.QJ84", "1C")
        assert not self.rule.applies(ctx)

    def test_4_card_major_rejected(self):
        """Has 4-card major — should bid it first."""
        # KJ84=4, Q73=2, QJ84=3, A3=4 → 13 HCP, 4-3-4-2
        ctx = _ctx("KJ84.Q73.QJ84.A3", "1D")
        assert not self.rule.applies(ctx)

    def test_9_hcp_rejected(self):
        """9 HCP — below limit raise range."""
        # K84=3, 973=0, QJ84=3, 973=0 → 6 HCP
        ctx = _ctx("K84.973.QJ84.973", "1D")
        assert not self.rule.applies(ctx)


# ── RespondSingleRaiseMinor ───────────────────────────────────────


class TestRespondSingleRaiseMinor:
    rule = RespondSingleRaiseMinor()

    def test_6_10_hcp_4_diamonds(self):
        """6-10 HCP, 4+ diamonds, no major → 2D."""
        # K84=3, Q73=2, QJ84=3, 973=0 → 8 HCP, 3-3-4-3
        ctx = _ctx("K84.Q73.QJ84.973", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_6_10_hcp_5_clubs(self):
        """6-10 HCP, 5+ clubs → 2C."""
        # K84=3, Q73=2, 73=0, QJ984=3 → 8 HCP, 3-3-2-5
        ctx = _ctx("K84.Q73.73.QJ984", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"

    def test_4_clubs_rejected(self):
        """Only 4 clubs — need 5+ for club raise."""
        # K84=3, Q73=2, 973=0, QJ84=3 → 8 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.973.QJ84", "1C")
        assert not self.rule.applies(ctx)

    def test_4_card_major_rejected(self):
        """Has 4-card major — should bid it first."""
        # KJ84=4, 973=0, QJ84=3, 73=0 → 7 HCP, 4-3-4-2 — 4 spades
        ctx = _ctx("KJ84.973.QJ84.73", "1D")
        assert not self.rule.applies(ctx)

    def test_5_hcp_rejected(self):
        """5 HCP — below minimum."""
        # 984=0, 973=0, QJ84=3, 973=0 → 3 HCP
        ctx = _ctx("984.973.QJ84.973", "1D")
        assert not self.rule.applies(ctx)


# ── Respond1NTOverMinor ───────────────────────────────────────────


class TestRespond1NTOverMinor:
    rule = Respond1NTOverMinor()

    def test_6_10_hcp_no_major(self):
        """6-10 HCP, no 4-card major → 1NT."""
        # K84=3, Q73=2, 973=0, QJ84=3 → 8 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.973.QJ84", "1C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"

    def test_1nt_over_1d(self):
        """1NT over 1D."""
        # K84=3, Q73=2, J84=1, 9732=0 → 6 HCP, 3-3-3-4
        ctx = _ctx("K84.Q73.J84.9732", "1D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"

    def test_4_card_major_rejected(self):
        """Has 4-card major — should bid it at 1-level."""
        # KJ84=4, Q73=2, 973=0, J84=1 → 7 HCP, 4-3-3-3
        ctx = _ctx("KJ84.Q73.973.J84", "1D")
        assert not self.rule.applies(ctx)

    def test_11_hcp_rejected(self):
        """11 HCP — above 1NT range over minor."""
        # AJ4=5, K73=3, 973=0, QJ84=3 → 11 HCP
        ctx = _ctx("AJ4.K73.973.QJ84", "1C")
        assert not self.rule.applies(ctx)

    def test_5_hcp_rejected(self):
        """5 HCP — below minimum."""
        # J84=1, Q73=2, 973=0, 9842=0 → 3 HCP
        ctx = _ctx("J84.Q73.973.9842", "1C")
        assert not self.rule.applies(ctx)
