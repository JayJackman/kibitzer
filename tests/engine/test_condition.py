"""Tests for the declarative condition system."""

from bridge.engine.condition import (
    All,
    Any,
    Balanced,
    BergenPtsRange,
    CheckResult,
    Computed,
    ConditionResult,
    HasSuitFit,
    HcpRange,
    MeetsOpeningStrength,
    Not,
    NoVoid,
    ShapeNot,
    SuitLength,
    SupportPtsRange,
    TotalPtsRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.model.auction import AuctionState, Seat
from bridge.model.board import Board
from bridge.model.card import Suit
from bridge.model.hand import Hand

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(
    pbn: str,
    seat: Seat = Seat.NORTH,
    dealer: Seat = Seat.NORTH,
) -> BiddingContext:
    """Build a BiddingContext for an opening-level decision."""
    from bridge.model.bid import PASS

    auction = AuctionState(dealer=dealer)
    offset = (seat.value - dealer.value) % 4
    for _ in range(offset):
        auction.add_bid(PASS)
    return BiddingContext(Board(hand=Hand.from_pbn(pbn), seat=seat, auction=auction))


# ---------------------------------------------------------------------------
# ConditionResult / CheckResult (data classes)
# ---------------------------------------------------------------------------


class TestConditionResult:
    def test_frozen(self) -> None:
        r = ConditionResult(passed=True, label="test", detail="test detail")
        assert r.passed is True
        assert r.label == "test"
        assert r.detail == "test detail"


class TestCheckResult:
    def test_fields(self) -> None:
        cr = ConditionResult(passed=True, label="x", detail="y")
        r = CheckResult(passed=True, results=(cr,))
        assert r.passed is True
        assert len(r.results) == 1


# ---------------------------------------------------------------------------
# HcpRange
# ---------------------------------------------------------------------------


class TestHcpRange:
    def test_in_range(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP
        r = HcpRange(15, 17).check(ctx)
        assert r.passed is True
        assert "17 HCP" in r.detail
        assert "15-17" in r.detail

    def test_below_range(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        r = HcpRange(15, 17).check(ctx)
        assert r.passed is False
        assert "0 HCP" in r.detail
        assert "need" in r.detail

    def test_above_range(self) -> None:
        ctx = _ctx("AKQJ2.AKQ.AK.A32")  # 27 HCP
        r = HcpRange(15, 17).check(ctx)
        assert r.passed is False

    def test_min_only(self) -> None:
        cond = HcpRange(min_hcp=12)
        assert cond.label == "12+ HCP"
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP
        assert cond.check(ctx).passed is True

    def test_max_only(self) -> None:
        cond = HcpRange(max_hcp=11)
        assert cond.label == "0-11 HCP"
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        assert cond.check(ctx).passed is True

    def test_label_both_bounds(self) -> None:
        assert HcpRange(15, 17).label == "15-17 HCP"


# ---------------------------------------------------------------------------
# TotalPtsRange
# ---------------------------------------------------------------------------


class TestTotalPtsRange:
    def test_in_range(self) -> None:
        # AKJ52.AKQ.AK.A32 = 26 HCP + 1 length = 27 total
        ctx = _ctx("AKJ52.AKQ.AK.A32")
        r = TotalPtsRange(min_pts=22).check(ctx)
        assert r.passed is True
        assert "total points" in r.detail

    def test_below_range(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 total points
        r = TotalPtsRange(min_pts=22).check(ctx)
        assert r.passed is False
        assert "need" in r.detail

    def test_label(self) -> None:
        assert TotalPtsRange(min_pts=22).label == "22+ total points"
        assert TotalPtsRange(min_pts=6, max_pts=10).label == "6-10 total points"


# ---------------------------------------------------------------------------
# Balanced
# ---------------------------------------------------------------------------


class TestBalanced:
    def test_balanced_strict(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")  # 4-3-3-3
        r = Balanced(strict=True).check(ctx)
        assert r.passed is True
        assert "balanced" in r.detail

    def test_not_balanced_strict(self) -> None:
        ctx = _ctx("AKJ52.KQ32.8.A73")  # 5-4-1-3 unbalanced
        r = Balanced(strict=True).check(ctx)
        assert r.passed is False
        assert "not balanced" in r.detail

    def test_semi_balanced(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5-3-2-3
        r = Balanced(strict=False).check(ctx)
        assert r.passed is True

    def test_label(self) -> None:
        assert Balanced(strict=True).label == "balanced"
        assert Balanced(strict=False).label == "semi-balanced"


# ---------------------------------------------------------------------------
# NoVoid
# ---------------------------------------------------------------------------


class TestNoVoid:
    def test_no_void(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # No void
        r = NoVoid().check(ctx)
        assert r.passed is True
        assert r.detail == "No void"

    def test_has_void(self) -> None:
        ctx = _ctx("AKQJT98.KQ3.84.2")  # 7-3-2-1, no void
        r = NoVoid().check(ctx)
        assert r.passed is True

    def test_actual_void(self) -> None:
        ctx = _ctx("AKQJT98.KQ32.84.")  # 7-4-2-0 void in clubs
        r = NoVoid().check(ctx)
        assert r.passed is False
        assert r.detail == "Has void"


# ---------------------------------------------------------------------------
# ShapeNot
# ---------------------------------------------------------------------------


class TestShapeNot:
    def test_not_matching(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5-3-3-2 sorted
        r = ShapeNot((4, 3, 3, 3)).check(ctx)
        assert r.passed is True

    def test_matching(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")  # 4-3-3-3 sorted
        r = ShapeNot((4, 3, 3, 3)).check(ctx)
        assert r.passed is False
        assert "is 4-3-3-3" in r.detail

    def test_label(self) -> None:
        assert ShapeNot((4, 3, 3, 3)).label == "not 4-3-3-3 shape"


# ---------------------------------------------------------------------------
# SuitLength
# ---------------------------------------------------------------------------


class TestSuitLength:
    def test_enough(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5 spades
        r = SuitLength(Suit.SPADES, min_len=4).check(ctx)
        assert r.passed is True
        assert "5 S" in r.detail

    def test_not_enough(self) -> None:
        ctx = _ctx("AK.KQ3.84.AJ7632")  # 2 spades
        r = SuitLength(Suit.SPADES, min_len=4).check(ctx)
        assert r.passed is False
        assert "need" in r.detail

    def test_max_only(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5 spades
        r = SuitLength(Suit.SPADES, max_len=4).check(ctx)
        assert r.passed is False

    def test_label(self) -> None:
        assert SuitLength(Suit.HEARTS, min_len=4).label == "4+ H"
        assert SuitLength(Suit.SPADES, min_len=5, max_len=7).label == "5-7 S"


# ---------------------------------------------------------------------------
# HasSuitFit
# ---------------------------------------------------------------------------


class TestHasSuitFit:
    def test_has_fit(self) -> None:
        ctx = _ctx("AK5.KQ32.84.A732")  # 3 spades
        cond = HasSuitFit(suit_fn=lambda _: Suit.SPADES, min_len=3)
        r = cond.check(ctx)
        assert r.passed is True
        assert "3 S" in r.detail

    def test_no_fit(self) -> None:
        ctx = _ctx("AK.KQ32.843.A732")  # 2 spades
        cond = HasSuitFit(suit_fn=lambda _: Suit.SPADES, min_len=3)
        r = cond.check(ctx)
        assert r.passed is False


# ---------------------------------------------------------------------------
# MeetsOpeningStrength
# ---------------------------------------------------------------------------


class TestMeetsOpeningStrength:
    def test_12_plus_hcp(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP, 1st seat
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is True
        assert "17 HCP" in r.detail

    def test_too_weak(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is False
        assert "need" in r.detail

    def test_rule_of_20(self) -> None:
        # 10 HCP, 5-5 shape: 10 + 5 + 5 = 20, passes Rule of 20
        ctx = _ctx("AKJ52.QT987.84.3")
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is True
        assert "Rule of 20" in r.detail

    def test_4th_seat_clear_opener(self) -> None:
        from bridge.model.bid import PASS

        # 4th seat with 13 HCP: opens regardless of spade length
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        ctx = BiddingContext(
            Board(
                hand=Hand.from_pbn("AKJ52.Q73.84.K73"),
                seat=Seat.WEST,
                auction=auction,
            )
        )
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is True
        assert "13+ opens in any seat" in r.detail

    def test_4th_seat_rule_of_15_passes(self) -> None:
        from bridge.model.bid import PASS

        # 4th seat: 12 HCP + 3 spades = 15, passes Rule of 15
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        ctx = BiddingContext(
            Board(
                hand=Hand.from_pbn("KJ5.Q73.842.AQ73"),
                seat=Seat.WEST,
                auction=auction,
            )
        )
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is True
        assert "Rule of 15" in r.detail

    def test_4th_seat_rule_of_15_fails(self) -> None:
        from bridge.model.bid import PASS

        # 4th seat: 12 HCP + 2 spades = 14, fails Rule of 15
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        auction.add_bid(PASS)
        ctx = BiddingContext(
            Board(
                hand=Hand.from_pbn("J9.9632.Q732.AKQ"),
                seat=Seat.WEST,
                auction=auction,
            )
        )
        r = MeetsOpeningStrength().check(ctx)
        assert r.passed is False
        assert "Rule of 15" in r.detail


# ---------------------------------------------------------------------------
# BergenPtsRange
# ---------------------------------------------------------------------------


class TestBergenPtsRange:
    def test_in_range(self) -> None:
        # Hand with shortness in a side suit gets bonus Bergen points
        ctx = _ctx("AKJT5.AQ65.7.A96")  # Strong hand with singleton D
        cond = BergenPtsRange(suit_fn=lambda _: Suit.SPADES, min_pts=16, max_pts=18)
        r = cond.check(ctx)
        # Bergen points depend on hand + trump suit evaluation
        assert "Bergen points" in r.detail

    def test_label(self) -> None:
        cond = BergenPtsRange(suit_fn=lambda _: Suit.SPADES, min_pts=16, max_pts=18)
        assert cond.label == "16-18 Bergen points"


# ---------------------------------------------------------------------------
# SupportPtsRange
# ---------------------------------------------------------------------------


class TestSupportPtsRange:
    def test_in_range(self) -> None:
        ctx = _ctx("K52.Q732.8.JT732")  # HCP + shortness for raising
        cond = SupportPtsRange(suit_fn=lambda _: Suit.HEARTS, min_pts=6, max_pts=10)
        r = cond.check(ctx)
        assert "support points" in r.detail

    def test_label(self) -> None:
        cond = SupportPtsRange(suit_fn=lambda _: Suit.HEARTS, min_pts=6, max_pts=10)
        assert cond.label == "6-10 support points"


# ---------------------------------------------------------------------------
# All combinator
# ---------------------------------------------------------------------------


class TestAll:
    def test_all_pass(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP, 5-3-3-2
        result = All(HcpRange(15, 17), Balanced()).check_all(ctx)
        assert result.passed is True
        assert len(result.results) == 2
        assert all(r.passed for r in result.results)

    def test_first_fails(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        result = All(HcpRange(15, 17), Balanced()).check_all(ctx)
        assert result.passed is False
        # Short-circuits: only the first condition is evaluated
        assert len(result.results) == 1
        assert result.results[0].passed is False

    def test_second_fails(self) -> None:
        ctx = _ctx("AKQJT.KQ32.8.A73")  # 19 HCP, 5-4-1-3 unbalanced
        result = All(HcpRange(15, 21), Balanced(strict=True)).check_all(ctx)
        assert result.passed is False
        assert len(result.results) == 2
        assert result.results[0].passed is True
        assert result.results[1].passed is False

    def test_computed_value_accessible_after_pass(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")
        comp = Computed(lambda c: Suit.SPADES, "test suit")
        result = All(HcpRange(min_hcp=12), comp).check_all(ctx)
        assert result.passed is True
        assert comp.value == Suit.SPADES

    def test_single_result_via_check(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")
        r = All(HcpRange(15, 17), Balanced()).check(ctx)
        assert r.passed is True
        assert isinstance(r, ConditionResult)

    def test_label(self) -> None:
        cond = All(HcpRange(15, 17), Balanced(strict=True))
        assert "15-17 HCP" in cond.label
        assert "balanced" in cond.label


# ---------------------------------------------------------------------------
# Any combinator
# ---------------------------------------------------------------------------


class TestAny:
    def test_first_path_passes(self) -> None:
        ctx = _ctx("AKJ52.KQ32.84.A7")  # 18 HCP, 5-4-2-2
        # Path 1: 15+ HCP (passes), Path 2: balanced (would also pass)
        result = Any(HcpRange(min_hcp=15), Balanced(strict=True)).check_all(ctx)
        assert result.passed is True

    def test_second_path_passes(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")  # 17 HCP, 4-3-3-3
        # Path 1: 20+ HCP (fails), Path 2: balanced strict (passes)
        result = Any(HcpRange(min_hcp=20), Balanced(strict=True)).check_all(ctx)
        assert result.passed is True

    def test_all_paths_fail(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        # Both paths fail on HCP
        result = Any(HcpRange(min_hcp=20), HcpRange(min_hcp=15)).check_all(ctx)
        assert result.passed is False

    def test_with_all_paths(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")  # 17 HCP, 4-3-3-3
        result = Any(
            All(HcpRange(min_hcp=20)),  # Fails
            All(HcpRange(15, 17), Balanced(strict=True)),  # Passes
        ).check_all(ctx)
        assert result.passed is True

    def test_single_result_via_check(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")
        r = Any(HcpRange(min_hcp=20), Balanced(strict=True)).check(ctx)
        assert r.passed is True
        assert isinstance(r, ConditionResult)


# ---------------------------------------------------------------------------
# Not combinator
# ---------------------------------------------------------------------------


class TestNot:
    def test_negates_passing(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP
        r = Not(HcpRange(15, 17)).check(ctx)
        # Inner passes, so Not fails
        assert r.passed is False
        assert "Has" in r.detail

    def test_negates_failing(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        r = Not(HcpRange(15, 17)).check(ctx)
        # Inner fails, so Not passes
        assert r.passed is True
        assert "No" in r.detail

    def test_custom_label_pass(self) -> None:
        ctx = _ctx("87654.432.T98.65")  # 0 HCP, not balanced
        r = Not(
            All(Balanced(strict=True), HcpRange(15, 17)),
            label="in 1NT range",
        ).check(ctx)
        assert r.passed is True
        assert r.detail == "Not in 1NT range"

    def test_custom_label_fail(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")  # 17 HCP, 4-3-3-3 balanced
        r = Not(
            All(Balanced(strict=True), HcpRange(15, 17)),
            label="in 1NT range",
        ).check(ctx)
        assert r.passed is False
        assert r.detail == "In 1NT range"

    def test_auto_label_pass(self) -> None:
        """Without custom label, prepends 'No' to inner label on pass."""
        ctx = _ctx("87654.432.T98.65")
        r = Not(HcpRange(15, 17)).check(ctx)
        assert r.passed is True
        assert r.detail == "No 15-17 HCP"

    def test_auto_label_fail(self) -> None:
        """Without custom label, prepends 'Has' to inner label on fail."""
        ctx = _ctx("AKJ52.KQ3.84.A73")
        r = Not(HcpRange(15, 17)).check(ctx)
        assert r.passed is False
        assert r.detail == "Has 15-17 HCP"

    def test_label_property_with_override(self) -> None:
        cond = Not(HcpRange(15, 17), label="in 1NT range")
        assert cond.label == "Not in 1NT range"

    def test_label_property_without_override(self) -> None:
        cond = Not(HcpRange(15, 17))
        assert cond.label == "No 15-17 HCP"


# ---------------------------------------------------------------------------
# Computed condition
# ---------------------------------------------------------------------------


class TestComputed:
    def test_passes_when_not_none(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")
        comp = Computed(lambda c: Suit.SPADES, "5+ card major")
        r = comp.check(ctx)
        assert r.passed is True
        assert "Found" in r.detail
        assert "5+ card major" in r.detail

    def test_fails_when_none(self) -> None:
        ctx = _ctx("AKJ5.KQ3.843.A73")
        comp = Computed(lambda c: None, "5+ card major")
        r = comp.check(ctx)
        assert r.passed is False
        assert "No 5+ card major found" in r.detail

    def test_value_after_pass(self) -> None:
        ctx = _ctx("AKJ52.KQ3.84.A73")
        comp = Computed(lambda c: Suit.SPADES, "5+ card major")
        comp.check(ctx)
        assert comp.value == Suit.SPADES

    def test_value_before_check_asserts(self) -> None:
        comp: Computed[Suit] = Computed(lambda c: Suit.SPADES, "test")
        import pytest

        with pytest.raises(AssertionError):
            _ = comp.value

    def test_cache_overwrites_on_new_check(self) -> None:
        """Each check() call overwrites the cached value."""
        calls = iter([Suit.SPADES, Suit.HEARTS])
        comp = Computed(lambda c: next(calls), "suit")
        ctx = _ctx("AKJ52.KQ3.84.A73")
        comp.check(ctx)
        assert comp.value == Suit.SPADES
        comp.check(ctx)
        assert comp.value == Suit.HEARTS

    def test_label(self) -> None:
        comp = Computed(lambda c: None, "5+ card major")
        assert comp.label == "5+ card major"

    def test_value_accessible_after_all_passes(self) -> None:
        """Computed.value is readable after All.check_all() passes."""
        ctx = _ctx("AKJ52.KQ3.84.A73")
        comp = Computed(lambda c: Suit.SPADES, "best major")
        result = All(HcpRange(min_hcp=12), comp).check_all(ctx)
        assert result.passed is True
        assert comp.value == Suit.SPADES


# ---------------------------------------------------------------------------
# @condition decorator
# ---------------------------------------------------------------------------


class TestConditionDecorator:
    def test_creates_condition(self) -> None:
        @condition("Hand has 5+ spades")
        def has_five_spades(ctx: BiddingContext) -> bool:
            return ctx.hand.suit_length(Suit.SPADES) >= 5

        assert has_five_spades.label == "Hand has 5+ spades"

    def test_check_passing(self) -> None:
        @condition("Hand has 5+ spades")
        def has_five_spades(ctx: BiddingContext) -> bool:
            return ctx.hand.suit_length(Suit.SPADES) >= 5

        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5 spades
        r = has_five_spades.check(ctx)
        assert r.passed is True
        assert r.detail == "Hand has 5+ spades"

    def test_check_failing(self) -> None:
        @condition("Hand has 5+ spades")
        def has_five_spades(ctx: BiddingContext) -> bool:
            return ctx.hand.suit_length(Suit.SPADES) >= 5

        ctx = _ctx("AK.KQ3.84.AJ7632")  # 2 spades
        r = has_five_spades.check(ctx)
        assert r.passed is False
        assert r.detail == "Not: Hand has 5+ spades"

    def test_callable_as_function(self) -> None:
        """Decorated functions can still be called directly to get a bool."""

        @condition("Hand has 5+ spades")
        def has_five_spades(ctx: BiddingContext) -> bool:
            return ctx.hand.suit_length(Suit.SPADES) >= 5

        ctx = _ctx("AKJ52.KQ3.84.A73")
        assert has_five_spades(ctx) is True

    def test_composable_with_all(self) -> None:
        @condition("Hand has 5+ spades")
        def has_five_spades(ctx: BiddingContext) -> bool:
            return ctx.hand.suit_length(Suit.SPADES) >= 5

        ctx = _ctx("AKJ52.KQ3.84.A73")  # 17 HCP, 5 spades
        result = All(HcpRange(15, 17), has_five_spades).check_all(ctx)
        assert result.passed is True

    def test_decorated_calls_decorated(self) -> None:
        """Decorated functions can call other decorated functions via __call__."""

        @condition("Hand has a major")
        def has_major(ctx: BiddingContext) -> bool:
            return (
                ctx.hand.suit_length(Suit.SPADES) >= 4
                or ctx.hand.suit_length(Suit.HEARTS) >= 4
            )

        @condition("Hand has a long major")
        def has_long_major(ctx: BiddingContext) -> bool:
            # Calls has_major as a function (via __call__)
            return has_major(ctx) and (
                ctx.hand.suit_length(Suit.SPADES) >= 5
                or ctx.hand.suit_length(Suit.HEARTS) >= 5
            )

        ctx = _ctx("AKJ52.KQ3.84.A73")  # 5 spades
        assert has_long_major(ctx) is True
        assert has_long_major.check(ctx).passed is True

    def test_usable_in_not(self) -> None:
        @condition("5+ card major")
        def has_five_major(ctx: BiddingContext) -> bool:
            return (
                ctx.hand.suit_length(Suit.SPADES) >= 5
                or ctx.hand.suit_length(Suit.HEARTS) >= 5
            )

        ctx = _ctx("AKJ5.KQ3.843.A73")  # 4 spades, 3 hearts
        r = Not(has_five_major).check(ctx)
        assert r.passed is True
        assert r.detail == "No 5+ card major"


# ---------------------------------------------------------------------------
# Integration: realistic rule-like composition
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_1nt_opening_conditions(self) -> None:
        """Simulate Open1NT conditions: 15-17 HCP, balanced."""
        conditions = All(HcpRange(15, 17), Balanced(strict=True))

        # 16 HCP, 4-3-3-3 balanced
        ctx = _ctx("AKJ5.KQ3.843.A73")
        result = conditions.check_all(ctx)
        assert result.passed is True
        assert len(result.results) == 2

    def test_1nt_fails_hcp(self) -> None:
        conditions = All(HcpRange(15, 17), Balanced(strict=True))
        ctx = _ctx("87654.432.T98.65")  # 0 HCP
        result = conditions.check_all(ctx)
        assert result.passed is False
        # Short-circuits on HCP
        assert len(result.results) == 1

    def test_1nt_fails_shape(self) -> None:
        conditions = All(HcpRange(15, 17), Balanced(strict=True))
        ctx = _ctx("AKJ52.KQ32.8.A73")  # 17 HCP, 5-4-1-3 unbalanced
        result = conditions.check_all(ctx)
        assert result.passed is False
        assert len(result.results) == 2
        assert result.results[0].passed is True  # HCP OK
        assert result.results[1].passed is False  # Shape fails

    def test_open_1major_with_not_and_computed(self) -> None:
        """Simulate Open1Major: opening strength, not in NT/2C range, 5+ major."""
        from bridge.evaluate import best_major

        find_major = Computed(lambda ctx: best_major(ctx.hand), "5+ card major")
        conditions = All(
            MeetsOpeningStrength(),
            Not(All(Balanced(strict=True), HcpRange(15, 17)), label="in 1NT range"),
            Not(All(Balanced(strict=True), HcpRange(20, 21)), label="in 2NT range"),
            Not(TotalPtsRange(min_pts=22), label="in 2C range"),
            find_major,
        )

        # 14 HCP, 5 spades, not balanced => should pass
        ctx = _ctx("AKJ52.Q73.84.A73")
        result = conditions.check_all(ctx)
        assert result.passed is True
        assert find_major.value == Suit.SPADES

    def test_stayman_any_paths(self) -> None:
        """Simulate Stayman with garbage vs regular path using Any."""

        @condition("4+ card major")
        def has_4_major(ctx: BiddingContext) -> bool:
            return (
                ctx.hand.suit_length(Suit.SPADES) >= 4
                or ctx.hand.suit_length(Suit.HEARTS) >= 4
            )

        @condition("5+ card major")
        def has_5_major(ctx: BiddingContext) -> bool:
            return (
                ctx.hand.suit_length(Suit.SPADES) >= 5
                or ctx.hand.suit_length(Suit.HEARTS) >= 5
            )

        conditions = Any(
            # Garbage Stayman: 4-4+ in majors, any HCP
            All(
                SuitLength(Suit.HEARTS, min_len=4),
                SuitLength(Suit.SPADES, min_len=4),
            ),
            # Regular Stayman: 8+ HCP, 4-card major, no 5+ major, not 4333
            All(
                HcpRange(min_hcp=8),
                has_4_major,
                Not(has_5_major),
                ShapeNot((4, 3, 3, 3)),
            ),
        )

        # 10 HCP, 4-4 in majors, 4-4-3-2 shape => garbage path passes
        ctx = _ctx("AK53.QJ42.J73.T8")
        result = conditions.check_all(ctx)
        assert result.passed is True
