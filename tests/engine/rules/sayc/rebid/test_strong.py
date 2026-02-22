"""Tests for opener rebids after 2C opening -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.rebid.strong import (
    Rebid2NTAfter2C,
    Rebid2NTAfter2COffshape,
    Rebid3NTAfter2C,
    RebidNTAfterPositive2C,
    RebidRaiseAfterPositive2C,
    RebidSuitAfter2C,
    RebidSuitAfterPositive2C,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx_after_2d(pbn: str) -> BiddingContext:
    """Build a BiddingContext where I opened 2C, partner responded 2D.

    South opens 2C, West passes, North responds 2D, East passes,
    South (opener) rebids.
    """
    auction = AuctionState(dealer=Seat.SOUTH)
    auction.add_bid(parse_bid("2C"))  # I (S) open 2C
    auction.add_bid(PASS)  # LHO (W) passes
    auction.add_bid(parse_bid("2D"))  # Partner (N) responds 2D waiting
    auction.add_bid(PASS)  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


def _ctx_after_positive(pbn: str, response: str) -> BiddingContext:
    """Build a BiddingContext where I opened 2C, partner made a positive response.

    South opens 2C, West passes, North responds with given bid, East passes,
    South (opener) rebids.
    """
    auction = AuctionState(dealer=Seat.SOUTH)
    auction.add_bid(parse_bid("2C"))  # I (S) open 2C
    auction.add_bid(PASS)  # LHO (W) passes
    auction.add_bid(parse_bid(response))  # Partner (N) positive response
    auction.add_bid(PASS)  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# -- Rebid2NTAfter2C ----------------------------------------------------------


class TestRebid2NTAfter2C:
    rule = Rebid2NTAfter2C()

    def test_22_hcp_balanced(self) -> None:
        """22 HCP, balanced -> 2NT."""
        # 22 HCP, 4-3-3-3 balanced
        ctx = _ctx_after_2d("AKQ3.AJ4.KQ3.K43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_24_hcp_balanced(self) -> None:
        """24 HCP, balanced -> 2NT."""
        # AKQ3.AQ4.AQ3.K43 = A=4+K=3+Q=2+A=4+Q=2+A=4+Q=2+K=3 = 24
        ctx = _ctx_after_2d("AKQ3.AQ4.AQ3.K43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_25_hcp_balanced_rejected(self) -> None:
        """25 HCP, balanced -> should bid 3NT, not 2NT."""
        # AKQ3.AQ4.AK3.K43 = A=4+K=3+Q=2+A=4+Q=2+A=4+K=3+K=3 = 25
        ctx = _ctx_after_2d("AKQ3.AQ4.AK3.K43")
        assert not self.rule.applies(ctx)

    def test_22_hcp_unbalanced_rejected(self) -> None:
        """22 HCP, unbalanced -> should bid suit."""
        # 22 HCP, 6-3-2-2 unbalanced
        ctx = _ctx_after_2d("AKQJ32.AK4.KQ.32")
        assert not self.rule.applies(ctx)

    def test_not_after_positive(self) -> None:
        """Does not apply after positive response."""
        ctx = _ctx_after_positive("AKQ3.AJ4.KQ3.K43", "2H")
        assert not self.rule.applies(ctx)


# -- Rebid3NTAfter2C ----------------------------------------------------------


class TestRebid3NTAfter2C:
    rule = Rebid3NTAfter2C()

    def test_25_hcp_balanced(self) -> None:
        """25 HCP, balanced -> 3NT."""
        # AKQ3.AQ4.AK3.K43 = A=4+K=3+Q=2+A=4+Q=2+A=4+K=3+K=3 = 25
        ctx = _ctx_after_2d("AKQ3.AQ4.AK3.K43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_24_hcp_rejected(self) -> None:
        """24 HCP -> should bid 2NT, not 3NT."""
        # AKQ3.AQ4.AQ3.K43 = 24 HCP
        ctx = _ctx_after_2d("AKQ3.AQ4.AQ3.K43")
        assert not self.rule.applies(ctx)


# -- RebidSuitAfter2C ---------------------------------------------------------


class TestRebidSuitAfter2C:
    rule = RebidSuitAfter2C()

    def test_5_spades(self) -> None:
        """5+ spades, unbalanced -> 2S."""
        # 21 HCP, 5-5-1-2 unbalanced
        ctx = _ctx_after_2d("AKQJ2.AK432.A.32")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        # Longest suits are 5S and 5H; spades (higher) wins
        assert str(result.bid) == "2S"

    def test_6_hearts(self) -> None:
        """6+ hearts -> 2H."""
        # 21 HCP, 6 hearts
        ctx = _ctx_after_2d("AK2.AKQ432.A.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_5_clubs(self) -> None:
        """5+ clubs -> 3C."""
        # 20 HCP, 3-4-1-5 unbalanced, 5 clubs
        ctx = _ctx_after_2d("AK3.AK43.2.AQ432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_5_diamonds(self) -> None:
        """5+ diamonds -> 3D."""
        # AK3.AK4.AQ432.32 = A=4+K=3+A=4+K=3+A=4+Q=2 = 20 HCP, 5 diamonds
        ctx = _ctx_after_2d("AK3.AK4.AQ432.32")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_no_5_card_suit_rejected(self) -> None:
        """No 5+ card suit -> does not apply."""
        # AKQ3.AJ4.KQ3.K43 = 22 HCP, 4-3-3-3 (no 5+ suit)
        ctx = _ctx_after_2d("AKQ3.AJ4.KQ3.K43")
        assert not self.rule.applies(ctx)


# -- Rebid2NTAfter2COffshape ----------------------------------------------------


class TestRebid2NTAfter2COffshape:
    rule = Rebid2NTAfter2COffshape()

    def test_4441_bids_2nt(self) -> None:
        """4-4-4-1 shape with 22+ HCP -> 2NT despite singleton."""
        # AKJ4.AKQ4.KQJ4.2 — 22 HCP, 4-4-4-1
        ctx = _ctx_after_2d("AKJ4.AKQ4.KQJ4.2")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_4441_singleton_club(self) -> None:
        """4-4-4-1 with singleton spade."""
        # 2.AKQ4.AKJ4.AKJ4 — 23 HCP, 1-4-4-4
        ctx = _ctx_after_2d("2.AKQ4.AKJ4.AKJ4")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_balanced_rejected(self) -> None:
        """Balanced hands use the standard Rebid2NTAfter2C rule."""
        # AKQ3.AJ4.KQ3.K43 — 22 HCP, balanced 4-3-3-3
        ctx = _ctx_after_2d("AKQ3.AJ4.KQ3.K43")
        assert not self.rule.applies(ctx)

    def test_5_card_suit_rejected(self) -> None:
        """Hands with a 5+ suit use RebidSuitAfter2C instead."""
        # AKQJ2.AK432.A.32 — 21 HCP, 5-5-1-2
        ctx = _ctx_after_2d("AKQJ2.AK432.A.32")
        assert not self.rule.applies(ctx)

    def test_not_after_positive(self) -> None:
        """Does not apply after positive response."""
        ctx = _ctx_after_positive("AKJ4.AKQ4.KQJ4.2", "2H")
        assert not self.rule.applies(ctx)


# -- RebidRaiseAfterPositive2C ------------------------------------------------


class TestRebidRaiseAfterPositive2C:
    rule = RebidRaiseAfterPositive2C()

    def test_4_hearts_support(self) -> None:
        """Partner bid 2H, opener has 4+ hearts -> raise to 3H."""
        # AK32.AK43.AK.432 = A=4+K=3+A=4+K=3+A=4+K=3 = 21 HCP, 4 hearts
        ctx = _ctx_after_positive("AK32.AK43.AK.432", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_4_spades_support(self) -> None:
        """Partner bid 2S, opener has 4+ spades -> raise to 3S."""
        ctx = _ctx_after_positive("AK43.AK32.AK.432", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_raise_3c_to_4c(self) -> None:
        """Partner bid 3C, opener has 4+ clubs -> raise to 4C."""
        ctx = _ctx_after_positive("AK32.AK3.A2.K432", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"

    def test_3_card_support_rejected(self) -> None:
        """Only 3 cards in partner's suit -> no raise."""
        # AK32.AK3.AK2.432 = 4 spades, 3 hearts, 3 diamonds, 3 clubs
        ctx = _ctx_after_positive("AK32.AK3.AK2.432", "2H")
        assert not self.rule.applies(ctx)

    def test_not_after_2nt_positive(self) -> None:
        """Does not apply after 2NT positive (no suit to raise)."""
        ctx = _ctx_after_positive("AK32.AK43.AK.432", "2NT")
        assert not self.rule.applies(ctx)

    def test_not_after_2d_waiting(self) -> None:
        """Does not apply after 2D waiting."""
        ctx = _ctx_after_2d("AK32.AK43.AK.432")
        assert not self.rule.applies(ctx)


# -- RebidSuitAfterPositive2C ------------------------------------------------


class TestRebidSuitAfterPositive2C:
    rule = RebidSuitAfterPositive2C()

    def test_5_spades_after_2h(self) -> None:
        """Partner bid 2H, opener has 5+ spades -> 2S."""
        # AKQJ2.A32.AK.432 = A=4+K=3+Q=2+J=1+A=4+A=4+K=3 = 21, 5 spades
        ctx = _ctx_after_positive("AKQJ2.A32.AK.432", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_5_hearts_after_2s(self) -> None:
        """Partner bid 2S, opener has 5+ hearts -> 3H (higher level)."""
        # A32.AKQJ2.AK.432 = 21 HCP, 5 hearts
        ctx = _ctx_after_positive("A32.AKQJ2.AK.432", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_5_spades_after_3c(self) -> None:
        """Partner bid 3C, opener has 5+ spades -> 3S."""
        ctx = _ctx_after_positive("AKQJ2.A32.AK.432", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_5_clubs_after_2h(self) -> None:
        """Partner bid 2H, opener has 5+ clubs -> 3C."""
        # AK2.A32.AK.AQ432 = A=4+K=3+A=4+A=4+K=3+A=4+Q=2 = 24, 5 clubs
        ctx = _ctx_after_positive("AK2.A32.AK.AQ432", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_suit_after_2nt_positive(self) -> None:
        """Partner bid 2NT, opener has 5+ spades -> 3S."""
        # AKQJ2.AK3.AK.432 = A=4+K=3+Q=2+J=1+A=4+K=3+A=4+K=3 = 24, 5 spades
        ctx = _ctx_after_positive("AKQJ2.AK3.AK.432", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_no_5_card_suit_rejected(self) -> None:
        """No 5+ card suit different from partner's -> no suit bid."""
        # AK32.AK32.AK.432 = 4 in each suit except 2 clubs. After 2H, no 5+ unbid suit.
        ctx = _ctx_after_positive("AK32.AK32.AK.432", "2H")
        assert not self.rule.applies(ctx)


# -- RebidNTAfterPositive2C --------------------------------------------------


class TestRebidNTAfterPositive2C:
    rule = RebidNTAfterPositive2C()

    def test_3nt_after_2h(self) -> None:
        """After positive 2H, balanced opener -> 3NT."""
        # AK32.A32.AK3.K32 = A=4+K=3+A=4+A=4+K=3+K=3 = 21
        ctx = _ctx_after_positive("AK32.A32.AK3.K32", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_3nt_after_2nt(self) -> None:
        """After positive 2NT, balanced opener -> 3NT."""
        ctx = _ctx_after_positive("AK32.A32.AK3.K32", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_not_after_2d(self) -> None:
        """Does not apply after 2D waiting."""
        ctx = _ctx_after_2d("AK32.A32.AK3.K32")
        assert not self.rule.applies(ctx)


# -- Priority conflicts -------------------------------------------------------


class TestPriorityConflicts2CRebid:
    """Verify priority ordering resolves ambiguities correctly."""

    def test_balanced_22_prefers_2nt_over_suit(self) -> None:
        """22 HCP balanced with 5+ suit -> 2NT wins over suit."""
        # AKQ32.AJ4.KQ3.K4 = A=4+K=3+Q=2+A=4+J=1+K=3+Q=2+K=3 = 22, balanced 5-3-3-2
        r2nt = Rebid2NTAfter2C()
        rsuit = RebidSuitAfter2C()
        ctx = _ctx_after_2d("AKQ32.AJ4.KQ3.K4")
        assert r2nt.applies(ctx)
        assert rsuit.applies(ctx)
        assert r2nt.priority > rsuit.priority

    def test_raise_beats_suit_after_positive(self) -> None:
        """4+ support beats bidding own suit."""
        rraise = RebidRaiseAfterPositive2C()
        rsuit = RebidSuitAfterPositive2C()
        # 4 hearts + 5 spades
        ctx = _ctx_after_positive("AKQJ2.AK43.AK.32", "2H")
        assert rraise.applies(ctx)
        assert rsuit.applies(ctx)
        assert rraise.priority > rsuit.priority

    def test_suit_beats_3nt_after_positive(self) -> None:
        """5+ own suit beats 3NT catch-all."""
        rsuit = RebidSuitAfterPositive2C()
        rnt = RebidNTAfterPositive2C()
        ctx = _ctx_after_positive("AKQJ2.A32.AK.432", "2H")
        assert rsuit.applies(ctx)
        assert rnt.applies(ctx)
        assert rsuit.priority > rnt.priority


# -- Guard: not after other openings -------------------------------------------


class TestNotAfterOtherOpenings:
    """Ensure 2C rebid rules don't fire after other openings."""

    def test_not_after_1nt_opening(self) -> None:
        """Rules should not apply after 1NT opening."""
        auction = AuctionState(dealer=Seat.SOUTH)
        auction.add_bid(parse_bid("1NT"))
        auction.add_bid(PASS)
        auction.add_bid(parse_bid("2D"))
        auction.add_bid(PASS)
        hand = Hand.from_pbn("AKQ3.AJ4.KQ3.K43")
        ctx = BiddingContext(Board(hand=hand, seat=Seat.SOUTH, auction=auction))
        assert not Rebid2NTAfter2C().applies(ctx)
        assert not RebidSuitAfter2C().applies(ctx)
