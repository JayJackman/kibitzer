"""Tests for opener's rebid rules — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.rebid.suit import (
    Rebid1NT,
    Rebid2NTAfter2Over1,
    Rebid2NTAfterRaiseMinor,
    Rebid2NTOver1NT,
    Rebid3NTAfter2Over1,
    Rebid3NTAfterRaiseMinor,
    Rebid3NTOver1NT,
    Rebid5mAfterLimitRaiseMinor,
    RebidAcceptLimitRaiseMajor,
    RebidDeclineLimitRaise,
    RebidDoubleJumpRaiseResponder,
    RebidDoubleJumpRebidOwnSuit,
    RebidGameAfterRaiseMajor,
    RebidHelpSuitGameTry,
    RebidInviteAfterRaiseMajor,
    RebidJacoby3LevelShortness,
    RebidJacoby3Major,
    RebidJacoby3NT,
    RebidJacoby4LevelSource,
    RebidJacoby4Major,
    RebidJumpRaiseResponder,
    RebidJumpRebidOver1NT,
    RebidJumpRebidOwnSuit,
    RebidJumpShiftNewSuit,
    RebidJumpShiftOver1NT,
    RebidJumpTo2NT,
    RebidMinorAfter2NTMinor,
    RebidNewLowerSuitOver1NT,
    RebidNewSuitAfter2Over1,
    RebidNewSuitAfterJumpShift,
    RebidNewSuitNonreverse,
    RebidNTAfter2NTMinor,
    RebidNTAfterJumpShift,
    RebidOwnSuit,
    RebidOwnSuitAfterJumpShift,
    RebidPassAfter3NT,
    RebidPassAfterGameRaise,
    RebidPassAfterRaise,
    RebidPassOver1NT,
    RebidRaise2Over1Responder,
    RebidRaiseAfterJumpShift,
    RebidRaiseResponder,
    RebidReverse,
    RebidShowMajorAfter2NTMinor,
    RebidSuitAfter2Over1,
    RebidSuitOver1NT,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import Bid, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str, opening: str, response: str) -> BiddingContext:
    """Build a BiddingContext where opener (North) rebids after a response."""
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))  # N opens
    auction.add_bid(Bid.make_pass())  # E passes
    auction.add_bid(parse_bid(response))  # S responds
    auction.add_bid(Bid.make_pass())  # W passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.NORTH, auction=auction)
    )


# ── After Single Raise of Major ─────────────────────────────────────


class TestGameAfterRaiseMajor:
    rule = RebidGameAfterRaiseMajor()

    def test_19_bergen_bids_game(self) -> None:
        # AKJ52.A3.K84.A73 — 19 HCP, 5-2-3-3, bergen=19
        ctx = _ctx("AKJ52.A3.K84.A73", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_singleton_boosts_bergen(self) -> None:
        # AKJ52.Q3.8.AK732 — 17 HCP, 5-2-1-5, bergen=20
        ctx = _ctx("AKJ52.Q3.8.AK732", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_17_hcp_flat_not_enough(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, 5-3-2-3, bergen=17
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)

    def test_hearts(self) -> None:
        # AK3.AKJ52.K84.A7 — 19 HCP, bergen=19
        ctx = _ctx("AK3.AKJ52.K84.A7", "1H", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_minor_raise_rejected(self) -> None:
        # AK3.A73.AKJ52.A7 — 19 HCP
        ctx = _ctx("AK3.A73.AKJ52.A7", "1D", "2D")
        assert not self.rule.applies(ctx)


class TestInviteAfterRaiseMajor:
    rule = RebidInviteAfterRaiseMajor()

    def test_17_bergen_invites(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, 5-3-2-3, bergen=17
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_15_bergen_too_low(self) -> None:
        # KJ852.KQ3.84.A73 — 13 HCP, bergen=13
        ctx = _ctx("KJ852.KQ3.84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)

    def test_19_bergen_too_high(self) -> None:
        # AKJ52.A3.K84.A73 — 19 HCP, bergen=19
        ctx = _ctx("AKJ52.A3.K84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)


class TestPassAfterRaise:
    rule = RebidPassAfterRaise()

    def test_minimum_passes(self) -> None:
        # KJ852.KQ3.84.A73 — 13 HCP, bergen=13
        ctx = _ctx("KJ852.KQ3.84.A73", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass

    def test_strong_hand_does_not_pass(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, bergen=17
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)

    def test_minor_raise_passes(self) -> None:
        # A73.KQ3.KJ852.84 — 13 HCP, bergen=13
        ctx = _ctx("A73.KQ3.KJ852.84", "1D", "2D")
        assert self.rule.applies(ctx)


# ── After Limit Raise of Major ──────────────────────────────────────


class TestAcceptLimitRaiseMajor:
    rule = RebidAcceptLimitRaiseMajor()

    def test_17_bergen_accepts(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, bergen=17
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_15_bergen_accepts(self) -> None:
        # AKJ52.K73.84.A73 — 15 HCP, bergen=15
        ctx = _ctx("AKJ52.K73.84.A73", "1S", "3S")
        assert self.rule.applies(ctx)

    def test_14_bergen_declines(self) -> None:
        # KJ852.Q73.84.A73 — 11 HCP, bergen=11
        ctx = _ctx("KJ852.Q73.84.A73", "1S", "3S")
        assert not self.rule.applies(ctx)


class TestDeclineLimitRaise:
    rule = RebidDeclineLimitRaise()

    def test_minimum_declines(self) -> None:
        # KJ852.Q73.84.A73 — 11 HCP, bergen=11
        ctx = _ctx("KJ852.Q73.84.A73", "1S", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass

    def test_strong_does_not_decline(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, bergen=17
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "3S")
        assert not self.rule.applies(ctx)

    def test_minor_limit_raise_declines(self) -> None:
        # Q73.A73.KJ852.84 — 11 HCP, bergen=11
        ctx = _ctx("Q73.A73.KJ852.84", "1D", "3D")
        assert self.rule.applies(ctx)


# ── After Raise of Minor ────────────────────────────────────────────


class TestRaiseMinorRebids:
    def test_3nt_after_single_raise_18_balanced(self) -> None:
        # KJ3.KQ3.AJ52.A73 — 18 HCP, balanced 3-3-4-3
        rule = Rebid3NTAfterRaiseMinor()
        ctx = _ctx("KJ3.KQ3.AJ52.A73", "1D", "2D")
        assert rule.applies(ctx)
        result = rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_3nt_after_single_raise_15_too_low(self) -> None:
        rule = Rebid3NTAfterRaiseMinor()
        # AK3.Q73.QJ52.K73 — 15 HCP, balanced
        ctx = _ctx("AK3.Q73.QJ52.K73", "1D", "2D")
        assert not rule.applies(ctx)

    def test_3nt_after_limit_raise_12_balanced(self) -> None:
        rule = Rebid3NTAfterRaiseMinor()
        # K73.Q73.AJ52.K73 — 12 HCP, balanced 3-3-4-3
        ctx = _ctx("K73.Q73.AJ52.K73", "1D", "3D")
        assert rule.applies(ctx)

    def test_2nt_after_single_raise_balanced(self) -> None:
        rule = Rebid2NTAfterRaiseMinor()
        # K73.Q73.AJ52.K73 — 12 HCP, balanced
        ctx = _ctx("K73.Q73.AJ52.K73", "1D", "2D")
        assert rule.applies(ctx)
        result = rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_5m_after_limit_raise_unbalanced(self) -> None:
        rule = Rebid5mAfterLimitRaiseMinor()
        # AK3.8.AKJ852.Q73 — 16 HCP, unbalanced, 6 diamonds
        ctx = _ctx("AK3.8.AKJ852.Q73", "1D", "3D")
        assert rule.applies(ctx)
        result = rule.select(ctx)
        assert str(result.bid) == "5D"

    def test_5m_balanced_rejected(self) -> None:
        rule = Rebid5mAfterLimitRaiseMinor()
        # AK3.K3.AJ852.Q73 — 15 HCP, semi-balanced
        ctx = _ctx("AK3.K3.AJ852.Q73", "1D", "3D")
        assert not rule.applies(ctx)


# ── After 1NT Response ──────────────────────────────────────────────


class Test3NTOver1NT:
    rule = Rebid3NTOver1NT()

    def test_19_balanced(self) -> None:
        # AKQ3.KJ8.AQ3.J84 — 20 HCP, balanced 4-3-3-3
        ctx = _ctx("AKQ3.KJ8.AQ3.J84", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_17_too_low(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "1NT")
        assert not self.rule.applies(ctx)


class Test2NTOver1NT:
    rule = Rebid2NTOver1NT()

    def test_18_balanced(self) -> None:
        # AKJ3.KQ8.Q84.A73 — 18 HCP, balanced 4-3-3-3
        ctx = _ctx("AKJ3.KQ8.Q84.A73", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"


class TestJumpShiftOver1NT:
    rule = RebidJumpShiftOver1NT()

    def test_19_pts_new_suit(self) -> None:
        # AKJ52.8.AK732.A3 — 19 HCP, 5-1-5-2, total=21, unbalanced
        ctx = _ctx("AKJ52.8.AK732.A3", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"  # jump in diamonds

    def test_balanced_rejected(self) -> None:
        # AKQ3.KJ8.AQ3.J84 — 20 HCP, balanced
        ctx = _ctx("AKQ3.KJ8.AQ3.J84", "1S", "1NT")
        assert not self.rule.applies(ctx)


class TestJumpRebidOver1NT:
    rule = RebidJumpRebidOver1NT()

    def test_6_card_15_hcp_total_17(self) -> None:
        # AKJ952.K73.84.A7 — 15 HCP, 6-3-2-2, total=17
        ctx = _ctx("AKJ952.K73.84.A7", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_5_card_suit_rejected(self) -> None:
        # AKJ52.KQ3.84.A73 — 17 HCP, 5-3-2-3, total=18
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "1NT")
        assert not self.rule.applies(ctx)


class TestNewLowerSuitOver1NT:
    rule = RebidNewLowerSuitOver1NT()

    def test_lower_suit_over_1s(self) -> None:
        # KJ852.84.K3.AQ73 — 13 HCP, 5-2-2-4, total=14
        ctx = _ctx("KJ852.84.K3.AQ73", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"

    def test_no_lower_suit_over_1c(self) -> None:
        # 843.K3.A73.KJ852 — 13 HCP, opened 1C, nothing lower
        ctx = _ctx("843.K3.A73.KJ852", "1C", "1NT")
        assert not self.rule.applies(ctx)


class TestRebidSuitOver1NT:
    rule = RebidSuitOver1NT()

    def test_6_card_minimum(self) -> None:
        # KJ8532.KQ3.8.A73 — 13 HCP, 6-3-1-3, total=15
        ctx = _ctx("KJ8532.KQ3.8.A73", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"


class TestPassOver1NT:
    rule = RebidPassOver1NT()

    def test_balanced_minimum_passes(self) -> None:
        # KJ852.KQ3.84.A73 — 13 HCP, balanced-ish minimum
        ctx = _ctx("KJ852.KQ3.84.A73", "1S", "1NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass


# ── After New Suit at 1-Level ───────────────────────────────────────


class TestJumpTo2NT:
    rule = RebidJumpTo2NT()

    def test_18_balanced_after_1h_1s(self) -> None:
        # AK32.KQJ52.Q3.K7 — 18 HCP, 4-5-2-2, semi-balanced
        ctx = _ctx("AK32.KQJ52.Q3.K7", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"


class TestJumpShiftNewSuit:
    rule = RebidJumpShiftNewSuit()

    def test_19_pts_new_suit_after_1_level(self) -> None:
        # A3.AKJ52.AK732.8 — 18 HCP, total=20, 2-5-5-1, unbalanced
        ctx = _ctx("A3.AKJ52.AK732.8", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"  # jump in diamonds


class TestJumpRaiseResponder:
    rule = RebidJumpRaiseResponder()

    def test_4_card_support_17_pts(self) -> None:
        # K842.AKJ52.Q7.A3 — 16 HCP, 4-5-2-2, total=17
        ctx = _ctx("K842.AKJ52.Q7.A3", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_3_card_support_rejected(self) -> None:
        # K84.AKJ52.Q73.A3 — 16 HCP, only 3 spades
        ctx = _ctx("K84.AKJ52.Q73.A3", "1H", "1S")
        assert not self.rule.applies(ctx)


class TestReverse:
    rule = RebidReverse()

    def test_reverse_1d_1s_2h(self) -> None:
        # A3.AQ73.AKJ52.73 — 16 HCP, total=17, D longer than H
        ctx = _ctx("A3.AQ73.AKJ52.73", "1D", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_equal_length_rejected(self) -> None:
        # A3.AQ73.AKJ5.732 — 4D = 4H, not strictly longer
        ctx = _ctx("A3.AQ73.AKJ5.732", "1D", "1S")
        assert not self.rule.applies(ctx)

    def test_16_pts_too_low(self) -> None:
        # 73.KQ73.AKJ52.73 — 13 HCP, total=14
        ctx = _ctx("73.KQ73.AKJ52.73", "1D", "1S")
        assert not self.rule.applies(ctx)


class TestJumpRebidOwnSuit:
    rule = RebidJumpRebidOwnSuit()

    def test_6_card_total_17(self) -> None:
        # K4.AKJ852.Q7.Q73 — 15 HCP, total=17, 6 hearts
        ctx = _ctx("K4.AKJ852.Q7.Q73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"


class TestRaiseResponder:
    rule = RebidRaiseResponder()

    def test_4_card_support_minimum(self) -> None:
        # K842.AKJ52.Q7.73 — 14 HCP, total=15, 4 spades
        ctx = _ctx("K842.AKJ52.Q7.73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_17_pts_too_high(self) -> None:
        # K842.AKJ52.Q7.A3 — 16 HCP, total=17
        ctx = _ctx("K842.AKJ52.Q7.A3", "1H", "1S")
        assert not self.rule.applies(ctx)


class TestNewSuitNonreverse:
    rule = RebidNewSuitNonreverse()

    def test_lower_suit_1h_1s(self) -> None:
        # K4.AKJ52.73.AQ73 — 15 HCP, total=16, clubs < hearts
        ctx = _ctx("K4.AKJ52.73.AQ73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"

    def test_1d_1h_bid_1s_at_1_level(self) -> None:
        # AQ73.73.AKJ52.K4 — 15 HCP, total=16, spades biddable at 1-level
        ctx = _ctx("AQ73.73.AKJ52.K4", "1D", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"  # non-reverse, biddable at 1-level


class TestRebidOwnSuit:
    rule = RebidOwnSuit()

    def test_6_card_minimum(self) -> None:
        # K4.KJ8532.Q7.A73 — 12 HCP, total=14, 6 hearts
        ctx = _ctx("K4.KJ8532.Q7.A73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"


class TestRebid1NT:
    rule = Rebid1NT()

    def test_balanced_12_14(self) -> None:
        # K73.AJ852.Q73.Q7 — 12 HCP, balanced 3-5-3-2
        ctx = _ctx("K73.AJ852.Q73.Q7", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1NT"

    def test_unbalanced_rejected(self) -> None:
        # K4.AJ852.Q732.Q7 — shape 2-5-4-2, not balanced
        ctx = _ctx("K4.AJ852.Q732.Q7", "1H", "1S")
        assert not self.rule.applies(ctx)


# ── After 2-Over-1 Response ─────────────────────────────────────────


class TestRaise2Over1Responder:
    rule = RebidRaise2Over1Responder()

    def test_4_card_support(self) -> None:
        # A7.AKJ52.73.K732 — 15 HCP, 2-5-2-4, 4 clubs
        ctx = _ctx("A7.AKJ52.73.K732", "1H", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"


class TestNewSuitAfter2Over1:
    rule = RebidNewSuitAfter2Over1()

    def test_third_suit(self) -> None:
        # AK42.AKJ52.Q7.73 — has 4 spades, opened 1H, resp 2C
        ctx = _ctx("AK42.AKJ52.Q7.73", "1H", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"


class TestRebidSuitAfter2Over1:
    rule = RebidSuitAfter2Over1()

    def test_6_card_rebid(self) -> None:
        # A4.AKJ852.Q7.K73 — 17 HCP, 6 hearts
        ctx = _ctx("A4.AKJ852.Q7.K73", "1H", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"


class TestNTAfter2Over1:
    def test_min_balanced(self) -> None:
        rule = Rebid2NTAfter2Over1()
        # K4.AJ852.Q73.K73 — 13 HCP, balanced 2-5-3-3
        ctx = _ctx("K4.AJ852.Q73.K73", "1H", "2C")
        assert rule.applies(ctx)
        result = rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_max_balanced(self) -> None:
        rule = Rebid3NTAfter2Over1()
        # KQ.AKJ52.Q73.K73 — 18 HCP, semi-balanced 2-5-3-3
        ctx = _ctx("KQ.AKJ52.Q73.K73", "1H", "2C")
        assert rule.applies(ctx)
        result = rule.select(ctx)
        assert str(result.bid) == "3NT"


# ── After 3NT Response (A1) ──────────────────────────────────────


class TestPassAfter3NT:
    rule = RebidPassAfter3NT()

    def test_pass_after_3nt_over_major(self) -> None:
        # AKJ52.KQ3.84.A73 — partner bid 3NT over 1S
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "3NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass

    def test_pass_after_3nt_over_minor(self) -> None:
        # A73.KQ3.AKJ52.84 — partner bid 3NT over 1D
        ctx = _ctx("A73.KQ3.AKJ52.84", "1D", "3NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass

    def test_does_not_apply_after_2nt(self) -> None:
        # Different response — 2NT, not 3NT
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "2NT")
        assert not self.rule.applies(ctx)


class TestPassAfterGameRaise:
    rule = RebidPassAfterGameRaise()

    def test_pass_after_4h(self) -> None:
        # A73.AKJ52.84.KQ3 — partner bid 4H preemptively
        ctx = _ctx("A73.AKJ52.84.KQ3", "1H", "4H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert result.bid.is_pass

    def test_pass_after_4s(self) -> None:
        # AKJ52.KQ3.84.A73 — partner bid 4S preemptively
        ctx = _ctx("AKJ52.KQ3.84.A73", "1S", "4S")
        assert self.rule.applies(ctx)

    def test_does_not_apply_to_minor(self) -> None:
        # 4D is not a preemptive game raise of a minor opening
        ctx = _ctx("A73.KQ3.AKJ52.84", "1D", "4D")
        assert not self.rule.applies(ctx)


# ── After Jacoby 2NT (A2) ────────────────────────────────────────


class TestJacoby3LevelShortness:
    rule = RebidJacoby3LevelShortness()

    def test_singleton_diamond(self) -> None:
        # AKJ52.KQ73.8.A73 — singleton diamond, 17 HCP
        ctx = _ctx("AKJ52.KQ73.8.A73", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"
        assert "singleton" in result.explanation

    def test_void_club(self) -> None:
        # AKJ52.KQ73.A873. — void in clubs, 16 HCP
        ctx = _ctx("AKJ52.KQ73.A873.", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"
        assert "void" in result.explanation

    def test_hearts_singleton(self) -> None:
        # 8.AKJ52.A873.KQ7 — singleton spade, opened 1H
        ctx = _ctx("8.AKJ52.A873.KQ7", "1H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_no_shortness_not_applicable(self) -> None:
        # AKJ52.KQ7.A73.83 — 5-3-3-2, no shortness
        ctx = _ctx("AKJ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)

    def test_not_applicable_over_minor(self) -> None:
        # Jacoby 2NT is only over 1M, not 1m
        ctx = _ctx("AKJ52.KQ73.8.A73", "1D", "2NT")
        assert not self.rule.applies(ctx)


class TestJacoby4LevelSource:
    rule = RebidJacoby4LevelSource()

    def test_5_card_side_suit_with_shortness(self) -> None:
        # AKJ52.KQ873.A7.3 - 5-5-2-1, has club singleton AND 5-card heart side suit.
        # Both this rule and the shortness rule apply; shortness wins on priority
        # (440 > 430), but a multi-option tool can surface both.
        ctx = _ctx("AKJ52.KQ873.A7.3", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_not_applicable_without_side_suit(self) -> None:
        # AKJ52.KQ7.A73.83 — no shortness, no 5-card side suit
        ctx = _ctx("AKJ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)


class TestJacoby3Major:
    rule = RebidJacoby3Major()

    def test_18_pts_no_shortness(self) -> None:
        # AKQ52.KQ7.A73.83 — 18 HCP, total=19, no shortness, no 5-card side suit
        ctx = _ctx("AKQ52.KQ7.A73.83", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_17_pts_too_low(self) -> None:
        # KQJ52.KQ7.A73.83 — 15 HCP, total=16
        ctx = _ctx("KQJ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)

    def test_has_shortness_not_applicable(self) -> None:
        # AKJ52.KQ73.8.A73 — has singleton diamond
        ctx = _ctx("AKJ52.KQ73.8.A73", "1S", "2NT")
        assert not self.rule.applies(ctx)


class TestJacoby3NT:
    rule = RebidJacoby3NT()

    def test_16_pts_no_shortness(self) -> None:
        # AKJ52.K73.A73.83 — 15 HCP, total=16, no shortness, no 5-card side suit
        ctx = _ctx("AKJ52.K73.A73.83", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_18_pts_too_high(self) -> None:
        # AKQ52.KQ7.A73.83 — 18 HCP, total=19
        ctx = _ctx("AKQ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)


class TestJacoby4Major:
    rule = RebidJacoby4Major()

    def test_12_pts_minimum(self) -> None:
        # KJ852.Q73.K73.A3 — 13 HCP, total=14, no shortness, no 5-card side suit
        ctx = _ctx("KJ852.Q73.K73.A3", "1S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_hearts(self) -> None:
        # Q73.KJ852.K73.A3 — same hand, hearts as trump
        ctx = _ctx("Q73.KJ852.K73.A3", "1H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_18_pts_too_high(self) -> None:
        # AKQ52.KQ7.A73.83 — total=19
        ctx = _ctx("AKQ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)


# ── After 2NT Over Minor (A3) ────────────────────────────────────


class TestShowMajorAfter2NTMinor:
    rule = RebidShowMajorAfter2NTMinor()

    def test_4_card_hearts(self) -> None:
        # A73.KQ83.AJ52.84 — 14 HCP, 4 hearts, opened 1D
        ctx = _ctx("A73.KQ83.AJ52.84", "1D", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_4_card_spades(self) -> None:
        # KQ83.A73.AJ52.84 — 4 spades, opened 1D
        ctx = _ctx("KQ83.A73.AJ52.84", "1D", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_both_majors_bids_hearts_first(self) -> None:
        # KQ83.AJ73.A852.8 — 4 spades, 4 hearts, opened 1D
        ctx = _ctx("KQ83.AJ73.A852.8", "1D", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"  # hearts first with both

    def test_no_major_not_applicable(self) -> None:
        # A73.K73.AJ52.Q84 — no 4-card major
        ctx = _ctx("A73.K73.AJ52.Q84", "1D", "2NT")
        assert not self.rule.applies(ctx)

    def test_not_applicable_over_major(self) -> None:
        # Jacoby 2NT (over major), not 2NT-over-minor
        ctx = _ctx("AKJ52.KQ73.8.A73", "1S", "2NT")
        assert not self.rule.applies(ctx)


class TestMinorAfter2NTMinor:
    rule = RebidMinorAfter2NTMinor()

    def test_6_card_minor_no_major(self) -> None:
        # A73.K73.AKJ852.8 — 15 HCP, 6 diamonds, no 4-card major
        ctx = _ctx("A73.K73.AKJ852.8", "1D", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_clubs(self) -> None:
        # K73.A73.8.AKJ852 — 6 clubs, opened 1C (13 cards: 3+3+1+6)
        ctx = _ctx("K73.A73.8.AKJ852", "1C", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_has_major_not_applicable(self) -> None:
        # AQ73.K73.AKJ852. — 4 spades, has 4-card major so show_major wins
        ctx = _ctx("AQ73.K73.AKJ852.", "1D", "2NT")
        assert not self.rule.applies(ctx)

    def test_5_card_minor_not_applicable(self) -> None:
        # A73.K73.AKJ52.83 — only 5 diamonds
        ctx = _ctx("A73.K73.AKJ52.83", "1D", "2NT")
        assert not self.rule.applies(ctx)


class TestNTAfter2NTMinor:
    rule = RebidNTAfter2NTMinor()

    def test_balanced_catch_all(self) -> None:
        # A73.K73.AJ52.Q84 — balanced, no 4-card major
        ctx = _ctx("A73.K73.AJ52.Q84", "1D", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_not_applicable_over_major(self) -> None:
        ctx = _ctx("AKJ52.KQ7.A73.83", "1S", "2NT")
        assert not self.rule.applies(ctx)


# ── After Jump Shift (A4) ────────────────────────────────────────


class TestRaiseAfterJumpShift:
    rule = RebidRaiseAfterJumpShift()

    def test_4_card_support(self) -> None:
        # AK73.AKJ52.Q7.73 — 4 spades, partner jump shifts to 2S after 1H
        ctx = _ctx("AK73.AKJ52.Q7.73", "1H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_3_card_support_not_applicable(self) -> None:
        # AK7.AKJ52.Q73.73 — only 3 spades
        ctx = _ctx("AK7.AKJ52.Q73.73", "1H", "2S")
        assert not self.rule.applies(ctx)

    def test_after_1c_jump_to_2d(self) -> None:
        # A73.K73.AQ83.KJ5 — 4 diamonds, partner jump shifts 1C→2D
        ctx = _ctx("A73.K73.AQ83.KJ5", "1C", "2D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"


class TestOwnSuitAfterJumpShift:
    rule = RebidOwnSuitAfterJumpShift()

    def test_6_card_suit(self) -> None:
        # K73.AKJ852.Q7.73 — 6 hearts, partner jump shifts to 2S after 1H
        ctx = _ctx("K73.AKJ852.Q7.73", "1H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_5_card_suit_not_applicable(self) -> None:
        # K73.AKJ52.Q73.73 — only 5 hearts
        ctx = _ctx("K73.AKJ52.Q73.73", "1H", "2S")
        assert not self.rule.applies(ctx)


class TestNewSuitAfterJumpShift:
    rule = RebidNewSuitAfterJumpShift()

    def test_third_suit(self) -> None:
        # K73.AKJ52.AQ73.7 — 4 diamonds, partner bid 2S (jump shift) after 1H
        ctx = _ctx("K73.AKJ52.AQ73.7", "1H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_no_third_suit_not_applicable(self) -> None:
        # K73.AKJ52.Q73.A7 — no 4-card side suit besides trump
        ctx = _ctx("K73.AKJ52.Q73.A7", "1H", "2S")
        assert not self.rule.applies(ctx)


class TestNTAfterJumpShift:
    rule = RebidNTAfterJumpShift()

    def test_balanced_catch_all(self) -> None:
        # K73.AKJ52.Q73.A7 — balanced, partner jump shifts to 2S after 1H
        # Cheapest NT above 2S is 2NT
        ctx = _ctx("K73.AKJ52.Q73.A7", "1H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_non_jump_shift_not_applicable(self) -> None:
        # 1H→1S is NOT a jump shift (cheapest level)
        ctx = _ctx("K73.AKJ52.Q73.A7", "1H", "1S")
        assert not self.rule.applies(ctx)

    def test_after_1d_jump_to_2h(self) -> None:
        # A73.K73.AKJ52.Q7 — partner jump shifts 1D→2H
        ctx = _ctx("A73.K73.AKJ52.Q7", "1D", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"  # cheapest NT above 2H

    def test_1d_1h_is_not_jump_shift(self) -> None:
        # 1D→1H is cheapest level, not a jump shift
        ctx = _ctx("A73.K73.AKJ52.Q7", "1D", "1H")
        assert not self.rule.applies(ctx)


# ── Help Suit Game Try (A5) ──────────────────────────────────────


class TestHelpSuitGameTry:
    rule = RebidHelpSuitGameTry()

    def test_game_try_picks_weakest_suit(self) -> None:
        # AKJ62.T753.8.AQ6 — 16 HCP, Bergen=18 (singleton +2)
        # S: AKJ62 = 8 HCP (trump)
        # H: T753  = 0 HCP ← weakest 3+ card side suit
        # D: 8     = skip (1 card)
        # C: AQ6   = 6 HCP
        ctx = _ctx("AKJ62.T753.8.AQ6", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_game_try_2s_after_heart_raise(self) -> None:
        # After 1H→2H, spades can be bid at the 2-level (2S)
        # T753.AKJ62.8.AQ6 — same shape, hearts opened
        # S: T753  = 0 HCP ← weakest
        # H: AKJ62 = 8 HCP (trump)
        # D: 8     = skip
        # C: AQ6   = 6 HCP
        ctx = _ctx("T753.AKJ62.8.AQ6", "1H", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_game_try_cheapest_bid_breaks_tie(self) -> None:
        # When two suits are equally weak, pick the cheapest bid
        # AKQJT.753.862.AK — 17 HCP, Bergen=17
        # H: 753 = 0 HCP, D: 862 = 0 HCP — tied in weakness
        # After 1S→2S: 3D vs 3H, 3D is cheaper
        ctx = _ctx("AKQJT.753.862.AK", "1S", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_minor_raise_not_applicable(self) -> None:
        # Game tries only apply after major raises
        ctx = _ctx("AJT62.AQ65.7.A96", "1D", "2D")
        assert not self.rule.applies(ctx)

    def test_15_bergen_too_low(self) -> None:
        # KJ852.Q73.84.A73 — 11 HCP, bergen=11
        ctx = _ctx("KJ852.Q73.84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)

    def test_19_bergen_too_high(self) -> None:
        # AKJ52.A3.K84.A73 — 19 HCP, bergen=19
        ctx = _ctx("AKJ52.A3.K84.A73", "1S", "2S")
        assert not self.rule.applies(ctx)

    def test_no_weak_suit_returns_none(self) -> None:
        # All side suits have 5+ HCP — no suit needs help
        # AJ852.AK3.KQ4.Q7 — 18 HCP, Bergen=18
        # H: AK3 = 7 HCP (> 4), D: KQ4 = 5 HCP (> 4), C: Q7 = 2 cards (skip)
        # No qualifying help suit → falls through to straight 3S invite
        ctx = _ctx("AJ852.AK3.KQ4.Q7", "1S", "2S")
        assert not self.rule.applies(ctx)


# ── Double-Jump Bids After New Suit 1-Level (A6) ─────────────────


class TestDoubleJumpRaiseResponder:
    rule = RebidDoubleJumpRaiseResponder()

    def test_19_pts_4_card_support(self) -> None:
        # KQ42.AKJ52.AQ.73 — 19 HCP, 4-5-2-2, total=20
        # 4 spades, partner bid 1S after 1H
        ctx = _ctx("KQ42.AKJ52.AQ.73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_17_pts_too_low(self) -> None:
        # K842.AKJ52.Q7.A3 — 16 HCP, total=17
        ctx = _ctx("K842.AKJ52.Q7.A3", "1H", "1S")
        assert not self.rule.applies(ctx)

    def test_3_card_support_not_applicable(self) -> None:
        # AK4.AKJ52.AQ7.73 — 20 HCP but only 3 spades
        ctx = _ctx("AK4.AKJ52.AQ7.73", "1H", "1S")
        assert not self.rule.applies(ctx)


class TestDoubleJumpRebidOwnSuit:
    rule = RebidDoubleJumpRebidOwnSuit()

    def test_19_pts_6_card_major(self) -> None:
        # AK.AKJ852.Q73.73 — 17 HCP, 6 hearts, total=19
        ctx = _ctx("AK.AKJ852.Q73.73", "1H", "1S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_6_card_minor_bids_5(self) -> None:
        # AK7.A73.AKJ852.7 — 19 HCP, total=21, 6 diamonds
        ctx = _ctx("AK7.A73.AKJ852.7", "1D", "1H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "5D"

    def test_17_pts_too_low(self) -> None:
        # K4.AKJ852.Q7.Q73 — 15 HCP, total=17
        ctx = _ctx("K4.AKJ852.Q7.Q73", "1H", "1S")
        assert not self.rule.applies(ctx)
