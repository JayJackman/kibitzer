"""Tests for preemptive opening bid rules — SAYC weak twos and preempts."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.opening.preempt import (
    OpenPreempt3,
    OpenPreempt4,
    OpenWeakTwo,
)
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


# ── OpenWeakTwo ──────────────────────────────────────────────────────


class TestOpenWeakTwo:
    rule = OpenWeakTwo()

    def test_6_card_hearts_7_hcp(self):
        """SAYC: 5-11 HCP, 6-card suit opens weak two."""
        # 84=0, KQJ842=6, 73=0, J84=1 → 7 HCP, 2-6-2-3
        ctx = _ctx("84.KQJ842.73.J84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"
        assert result.rule_name == "opening.weak_two"

    def test_6_card_spades(self):
        """Weak two in spades."""
        # KQT973=5, 84=0, 73=0, J84=1 → 6 HCP, 6-2-2-3
        ctx = _ctx("KQT973.84.73.J84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_6_card_diamonds(self):
        """Weak two in diamonds."""
        # 84=0, 73=0, KQJ842=6, J84=1 → 7 HCP, 2-2-6-3
        ctx = _ctx("84.73.KQJ842.J84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_6_card_clubs_not_allowed(self):
        """2C is reserved for strong opening — can't weak-two in clubs."""
        # 84=0, 73=0, J84=1, KQJ842=6 → 7 HCP, 2-2-3-6
        ctx = _ctx("84.73.J84.KQJ842")
        assert not self.rule.applies(ctx)

    def test_void_rejects(self):
        """No voids allowed for weak two."""
        # void in spades: 0-7-3-3
        ctx = _ctx(".KQJ8432.873.J84")
        assert not self.rule.applies(ctx)

    def test_outside_4_card_major_rejects(self):
        """No outside 4-card major allowed (4 spades + 6 hearts)."""
        # K843=3, KQJ842=6, 7=0, 84=0 → 9 HCP, 4-6-1-2
        # Rejected: has 4-card spade major outside hearts.
        # Also has a singleton diamond (not a void).
        ctx = _ctx("K843.KQJ842.7.84")
        assert not self.rule.applies(ctx)

    def test_outside_4_card_major_no_void(self):
        """No outside 4-card major, hand without void."""
        # K843=3, KQJ842=6, 73=0, 4=0 → 9 HCP, 4-6-2-1
        # Rejected for 4 spades outside hearts.
        ctx = _ctx("K843.KQJ842.73.4")
        assert not self.rule.applies(ctx)

    def test_only_5_card_suit_rejected(self):
        """Need exactly 6 cards, not 5."""
        # 84=0, AKJ52=8, Q73=2, J84=1 → 11 HCP, 2-5-3-3
        ctx = _ctx("84.AKJ52.Q73.J84")
        assert not self.rule.applies(ctx)

    def test_12_hcp_too_strong(self):
        """12+ HCP is too strong for a weak two."""
        # 84=0, AKJ842=8, A3=4, 984=0 → 12 HCP, 2-6-2-3
        ctx = _ctx("84.AKJ842.A3.984")
        assert not self.rule.applies(ctx)

    def test_3_hcp_too_weak(self):
        """3 HCP is below the 5 HCP minimum."""
        # 84=0, QJT842=3, 73=0, 984=0 → 3 HCP, 2-6-2-3
        ctx = _ctx("84.QJT842.73.984")
        assert not self.rule.applies(ctx)

    def test_poor_suit_quality_rejected(self):
        """Suit needs 2 of AKQ or 3 of AKQJT."""
        # 84=0, J98742=1, K3=3, A84=4 → 8 HCP, 2-6-2-3
        # Hearts: only J (1 of top 3 < 2, 1 of top 5 < 3). No quality.
        ctx = _ctx("84.J98742.K3.A84")
        assert not self.rule.applies(ctx)

    def test_10_hcp_6_card_opens_weak(self):
        """10 HCP with 6-card quality suit: weak two."""
        # 84=0, KQJ842=6, A3=4, 984=0 → 10 HCP, 2-6-2-3
        ctx = _ctx("84.KQJ842.A3.984")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"


# ── OpenPreempt3 ─────────────────────────────────────────────────────


class TestOpenPreempt3:
    rule = OpenPreempt3()

    def test_7_card_hearts_preempt(self):
        """SAYC: 7-card suit, below opening strength → 3-level preempt."""
        # 84=0, KQT9732=5, 73=0, 84=0 → 5 HCP, 2-7-2-2
        ctx = _ctx("84.KQT9732.73.84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"
        assert result.rule_name == "opening.preempt_3"

    def test_7_card_hearts_6_hcp(self):
        """Another 3H preempt hand."""
        # K4=3, QJT8432=3, 73=0, 84=0 → 6 HCP, 2-7-2-2
        ctx = _ctx("K4.QJT8432.73.84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_7_card_clubs(self):
        """3C preempt with 7-card club suit."""
        # 84=0, 73=0, 84=0, KQT9732=5 → 5 HCP, 2-2-2-7
        ctx = _ctx("84.73.84.KQT9732")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_12_hcp_too_strong(self):
        """12+ HCP should open at 1-level, not preempt."""
        # A4=4, AKJ9732=8, 73=0, 84=0 → 12 HCP, 2-7-2-2
        ctx = _ctx("A4.AKJ9732.73.84")
        assert not self.rule.applies(ctx)

    def test_poor_suit_quality_rejected(self):
        """7-card suit without quality doesn't preempt."""
        # 84=0, 9876432=0, K3=3, A4=4 → 7 HCP, 2-7-2-2, no quality in H
        ctx = _ctx("84.9876432.K3.A4")
        assert not self.rule.applies(ctx)

    def test_outside_4_card_major_rejected(self):
        """Don't preempt with an outside 4-card major."""
        # KJ43=4, 3=0, QJT9873=3, 4=0 → 7 HCP, 4-1-7-1
        # Has 4-card spade major outside diamonds.
        ctx = _ctx("KJ43.3.QJT9873.4")
        assert not self.rule.applies(ctx)


# ── OpenPreempt4 ─────────────────────────────────────────────────────


class TestOpenPreempt4:
    rule = OpenPreempt4()

    def test_8_card_minor_preempt(self):
        """SAYC: 8+ card suit opens at 4-level."""
        # 84=0, 73=0, KQJ98432=6, 4=0 → 6 HCP, 2-2-8-1
        ctx = _ctx("84.73.KQJ98432.4")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"
        assert result.rule_name == "opening.preempt_4"

    def test_7_card_major_opens_4(self):
        """SAYC: 4H/4S may be opened with 7+ cards."""
        # KQJT973=6, 84=0, 73=0, 84=0 → 6 HCP, 7-2-2-2
        ctx = _ctx("KQJT973.84.73.84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_7_card_minor_does_not_open_4(self):
        """7-card minor goes to 3-level, not 4-level."""
        # 84=0, 73=0, KQT9732=5, 84=0 → 5 HCP, 2-2-7-2
        ctx = _ctx("84.73.KQT9732.84")
        assert not self.rule.applies(ctx)

    def test_12_hcp_too_strong(self):
        """12+ HCP shouldn't preempt at 4-level."""
        # AKQJT973=10, 84=0, A3=4, 4=0 → 14 HCP, 7-2-2-2
        ctx = _ctx("AKQJT973.84.A3.4")
        assert not self.rule.applies(ctx)

    def test_poor_suit_quality_rejected(self):
        """8-card suit without quality doesn't preempt."""
        # 84=0, 73=0, 98765432=0, 4=0 → 0 HCP, 2-2-8-1
        ctx = _ctx("84.73.98765432.4")
        assert not self.rule.applies(ctx)
