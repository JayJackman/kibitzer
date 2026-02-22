"""Tests for opener rebids after preemptive openings -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.rebid.preempt import (
    Rebid3NTAfterFeatureAsk,
    RebidOwnSuitAfterFeatureAsk,
    RebidOwnSuitAfterNewSuit3Level,
    RebidOwnSuitAfterNewSuitWeakTwo,
    RebidPassAfter3Level,
    RebidPassAfter4Level,
    RebidPassAfterWeakTwo,
    RebidRaiseAfterNewSuit3Level,
    RebidRaiseNewSuitWeakTwo,
    RebidShowFeature,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx_weak_two(pbn: str, opening: str, response: str) -> BiddingContext:
    """Build a context: I opened a weak two, partner responded.

    South opens, West passes, North responds, East passes, South rebids.
    """
    auction = AuctionState(dealer=Seat.SOUTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    auction.add_bid(parse_bid(response))
    auction.add_bid(PASS)
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


def _ctx_3_level(pbn: str, opening: str, response: str) -> BiddingContext:
    """Build a context: I opened a 3-level preempt, partner responded."""
    auction = AuctionState(dealer=Seat.SOUTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    auction.add_bid(parse_bid(response))
    auction.add_bid(PASS)
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


def _ctx_4_level(pbn: str, opening: str, response: str) -> BiddingContext:
    """Build a context: I opened a 4-level preempt, partner responded."""
    auction = AuctionState(dealer=Seat.SOUTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    auction.add_bid(parse_bid(response))
    auction.add_bid(PASS)
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# ===========================================================================
# B4: Weak Two Rebids -- After 2NT Feature Ask
# ===========================================================================


class TestRebidShowFeature:
    rule = RebidShowFeature()

    def test_show_ace_feature(self) -> None:
        """Maximum with outside ace -> show feature."""
        # 10 HCP, opened 2H, ace of clubs is a feature
        ctx = _ctx_weak_two("43.KQJ432.43.A32", "2H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_show_protected_king_feature(self) -> None:
        """Maximum with protected king -> show feature."""
        # 9 HCP, opened 2S, Kx in clubs is a feature
        ctx = _ctx_weak_two("AQJ432.432.43.K2", "2S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_cheapest_feature(self) -> None:
        """Multiple features -> show cheapest."""
        # 11 HCP, opened 2H, A of clubs and K of spades -> show clubs (cheapest)
        ctx = _ctx_weak_two("K2.AQJ432.432.A2", "2H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_minimum_rejected(self) -> None:
        """8 HCP (minimum) -> does not show feature."""
        # 8 HCP, has ace of clubs but is minimum
        ctx = _ctx_weak_two("43.KJT432.432.A2", "2H", "2NT")
        assert not self.rule.applies(ctx)

    def test_not_after_new_suit(self) -> None:
        """Does not apply after new suit response."""
        ctx = _ctx_weak_two("43.AKJ432.432.A2", "2H", "2S")
        assert not self.rule.applies(ctx)


class TestRebid3NTAfterFeatureAsk:
    rule = Rebid3NTAfterFeatureAsk()

    def test_max_no_feature(self) -> None:
        """Maximum, no feature -> 3NT."""
        # 9 HCP, opened 2H, no outside ace or Kx+
        ctx = _ctx_weak_two("43.AKQ432.J32.43", "2H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_max_with_feature_rejected(self) -> None:
        """Maximum with feature -> should show feature, not 3NT."""
        # 10 HCP, has ace of clubs
        ctx = _ctx_weak_two("43.AKJ432.432.A2", "2H", "2NT")
        assert not self.rule.applies(ctx)

    def test_minimum_rejected(self) -> None:
        """Minimum -> does not bid 3NT."""
        # 7 HCP (min), no feature
        ctx = _ctx_weak_two("43.KQJ432.J32.43", "2H", "2NT")
        assert not self.rule.applies(ctx)


class TestRebidOwnSuitAfterFeatureAsk:
    rule = RebidOwnSuitAfterFeatureAsk()

    def test_minimum_sign_off(self) -> None:
        """Minimum (<=8 HCP) -> rebid own suit."""
        # 7 HCP, opened 2H
        ctx = _ctx_weak_two("43.KQJ432.Q32.43", "2H", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_minimum_spades(self) -> None:
        """Minimum, opened 2S -> rebid 3S."""
        ctx = _ctx_weak_two("KQJ432.43.Q32.43", "2S", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_maximum_rejected(self) -> None:
        """9+ HCP -> does not rebid own suit (should show feature or 3NT)."""
        ctx = _ctx_weak_two("43.AKQ432.J32.43", "2H", "2NT")
        assert not self.rule.applies(ctx)


# ===========================================================================
# B4: Weak Two Rebids -- After New Suit Response
# ===========================================================================


class TestRebidRaiseNewSuitWeakTwo:
    rule = RebidRaiseNewSuitWeakTwo()

    def test_raise_partner_suit(self) -> None:
        """3+ support for partner's suit -> raise."""
        # Opened 2H, partner bid 2S, 3 spades
        ctx = _ctx_weak_two("K32.KQJ432.43.43", "2H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_raise_3c_to_4c(self) -> None:
        """Raise partner's 3C to 4C."""
        # Opened 2S, partner bid 3C, 3 clubs
        ctx = _ctx_weak_two("AQJ432.43.43.K32", "2S", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"

    def test_2_card_support_rejected(self) -> None:
        """Only 2-card support -> no raise."""
        ctx = _ctx_weak_two("K2.KQJ432.432.43", "2H", "2S")
        assert not self.rule.applies(ctx)


class TestRebidOwnSuitAfterNewSuitWeakTwo:
    rule = RebidOwnSuitAfterNewSuitWeakTwo()

    def test_rebid_own_suit(self) -> None:
        """No fit -> rebid own suit."""
        # Opened 2H, partner bid 2S, 2 spades
        ctx = _ctx_weak_two("K2.KQJ432.432.43", "2H", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_rebid_spades(self) -> None:
        """Opened 2S, partner bid 3C, no fit -> 3S."""
        ctx = _ctx_weak_two("AQJ432.43.432.43", "2S", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"


# ===========================================================================
# B4: Weak Two Rebids -- Catch-all Pass
# ===========================================================================


class TestRebidPassAfterWeakTwo:
    rule = RebidPassAfterWeakTwo()

    def test_pass_after_raise(self) -> None:
        """Raise is to play -> pass."""
        ctx = _ctx_weak_two("43.KQJ432.432.43", "2H", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "Pass"

    def test_pass_after_3nt(self) -> None:
        """3NT is to play -> pass."""
        ctx = _ctx_weak_two("43.KQJ432.432.43", "2H", "3NT")
        assert self.rule.applies(ctx)

    def test_pass_after_game_raise(self) -> None:
        """Game raise is to play -> pass."""
        ctx = _ctx_weak_two("43.KQJ432.432.43", "2H", "4H")
        assert self.rule.applies(ctx)


# ===========================================================================
# B5: 3-Level Preempt Rebids
# ===========================================================================


class TestRebidRaiseAfterNewSuit3Level:
    rule = RebidRaiseAfterNewSuit3Level()

    def test_raise_3h_to_4h(self) -> None:
        """Opened 3C, partner bid 3H, 3+ hearts -> 4H."""
        ctx = _ctx_3_level("43.K32.4.KQJ5432", "3C", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_raise_3s_to_4s(self) -> None:
        """Opened 3D, partner bid 3S, 3 spades -> 4S."""
        ctx = _ctx_3_level("K32.43.QJT5432.4", "3D", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_2_card_support_rejected(self) -> None:
        """Only 2-card support -> no raise."""
        ctx = _ctx_3_level("K2.432.QJT5432.4", "3D", "3S")
        assert not self.rule.applies(ctx)


class TestRebidOwnSuitAfterNewSuit3Level:
    rule = RebidOwnSuitAfterNewSuit3Level()

    def test_rebid_own_suit_at_4(self) -> None:
        """No fit -> rebid own suit at 4-level."""
        # Opened 3C, partner bid 3H, 2 hearts
        ctx = _ctx_3_level("43.42.43.KQJ5432", "3C", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"


class TestRebidPassAfter3Level:
    rule = RebidPassAfter3Level()

    def test_pass_after_raise(self) -> None:
        """Raise is to play -> pass."""
        ctx = _ctx_3_level("43.43.43.KQJ5432", "3C", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "Pass"

    def test_pass_after_3nt(self) -> None:
        """3NT is to play -> pass."""
        ctx = _ctx_3_level("43.43.43.KQJ5432", "3C", "3NT")
        assert self.rule.applies(ctx)


# ===========================================================================
# B6: 4-Level Preempt Rebids
# ===========================================================================


class TestRebidPassAfter4Level:
    rule = RebidPassAfter4Level()

    def test_pass_after_5c(self) -> None:
        """Partner raised to 5C -> pass."""
        ctx = _ctx_4_level("43.4.43.AKQJ5432", "4C", "5C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "Pass"

    def test_not_after_weak_two(self) -> None:
        """Does not apply after weak two opening."""
        ctx = _ctx_weak_two("43.KQJ432.432.43", "2H", "3H")
        assert not self.rule.applies(ctx)


# ===========================================================================
# Priority Conflicts
# ===========================================================================


class TestWeakTwoRebidPriorities:
    """Verify priority ordering for weak two rebids."""

    def test_show_feature_beats_3nt(self) -> None:
        """Max with feature -> show feature wins over 3NT."""
        r_feat = RebidShowFeature()
        r_3nt = Rebid3NTAfterFeatureAsk()
        # 10 HCP, feature in clubs
        ctx = _ctx_weak_two("43.AKJ432.432.A2", "2H", "2NT")
        assert r_feat.applies(ctx)
        assert not r_3nt.applies(ctx)  # mutually exclusive
        assert r_feat.priority > r_3nt.priority

    def test_raise_beats_own_suit_after_new(self) -> None:
        """With 3+ support, raise wins over rebid own suit."""
        r_raise = RebidRaiseNewSuitWeakTwo()
        r_own = RebidOwnSuitAfterNewSuitWeakTwo()
        ctx = _ctx_weak_two("K32.KQJ432.43.43", "2H", "2S")
        assert r_raise.applies(ctx)
        assert r_own.applies(ctx)
        assert r_raise.priority > r_own.priority

    def test_own_suit_beats_pass_after_new(self) -> None:
        """Rebid own suit beats pass after new suit."""
        r_own = RebidOwnSuitAfterNewSuitWeakTwo()
        r_pass = RebidPassAfterWeakTwo()
        ctx = _ctx_weak_two("K2.KQJ432.432.43", "2H", "2S")
        assert r_own.applies(ctx)
        assert r_pass.applies(ctx)
        assert r_own.priority > r_pass.priority


# ===========================================================================
# Guard: not after other openings
# ===========================================================================


class TestNotAfterOtherOpenings:
    """Ensure preempt rebid rules don't fire after other openings."""

    def test_not_after_1nt_opening(self) -> None:
        """Rules should not apply after 1NT opening."""
        auction = AuctionState(dealer=Seat.SOUTH)
        auction.add_bid(parse_bid("1NT"))
        auction.add_bid(PASS)
        auction.add_bid(parse_bid("2NT"))
        auction.add_bid(PASS)
        hand = Hand.from_pbn("43.AKJ432.432.A2")
        ctx = BiddingContext(Board(hand=hand, seat=Seat.SOUTH, auction=auction))
        assert not RebidShowFeature().applies(ctx)
        assert not RebidPassAfterWeakTwo().applies(ctx)
