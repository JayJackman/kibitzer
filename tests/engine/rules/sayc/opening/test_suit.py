"""Tests for 1-level suit opening bid rules — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.opening.suit import Open1Major, Open1Minor, OpenPass
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, is_pass
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(
    pbn: str,
    seat: Seat = Seat.NORTH,
    dealer: Seat = Seat.NORTH,
) -> BiddingContext:
    """Build a BiddingContext for an opening decision.

    Passes are added for seats between dealer and the player.
    """
    auction = AuctionState(dealer=dealer)
    offset = (seat.value - dealer.value) % 4
    for _ in range(offset):
        auction.add_bid(PASS)
    return BiddingContext(Board(hand=Hand.from_pbn(pbn), seat=seat, auction=auction))


# ── Open1Major ───────────────────────────────────────────────────────


class TestOpen1Major:
    rule = Open1Major()

    def test_5_card_spades(self):
        """SAYC: 5-card major opens 1S."""
        # AKJ52=8, Q73=2, 84=0, A73=4 → 14 HCP, 5-3-2-3
        ctx = _ctx("AKJ52.Q73.84.A73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"
        assert result.rule_name == "opening.1_major"

    def test_5_card_hearts(self):
        """SAYC: 5-card major opens 1H."""
        # 84=0, AKJ52=8, Q73=2, A73=4 → 14 HCP, 2-5-3-3
        ctx = _ctx("84.AKJ52.Q73.A73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1H"

    def test_two_5_card_majors_bids_higher(self):
        """SAYC: With two 5-card suits, bid the higher-ranking."""
        # AKJ52=8, AQT73=6, 8=0, 73=0 → 14 HCP, 5-5-1-2
        ctx = _ctx("AKJ52.AQT73.8.73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"

    def test_6_card_major_opens_1(self):
        """6-card major with opening strength opens at 1-level."""
        # AKJ532=8, Q73=2, A4=4, 73=0 → 14 HCP, 6-3-2-2
        ctx = _ctx("AKJ532.Q73.A4.73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"

    def test_4_card_major_rejected(self):
        """Must have 5+ cards in a major — SAYC five-card majors."""
        # AKJ5=8, Q73=2, 843=0, A73=4 → 14 HCP, 4-3-3-3
        ctx = _ctx("AKJ5.Q73.843.A73")
        assert not self.rule.applies(ctx)

    def test_balanced_15_17_rejected(self):
        """15-17 balanced opens 1NT, not 1-major."""
        # AKJ52=8, KQ3=5, 84=0, A73=4 → 17 HCP, 5-3-2-3 balanced
        ctx = _ctx("AKJ52.KQ3.84.A73")
        assert not self.rule.applies(ctx)

    def test_22_total_pts_rejected(self):
        """22+ total points opens 2C, not 1-major."""
        # AKQJ52=10, AKQ=9, 84=0, A3=4 → 23 HCP, total=25, 6-3-2-2
        ctx = _ctx("AKQJ52.AKQ.84.A3")
        assert not self.rule.applies(ctx)

    def test_10_hcp_below_opening_strength(self):
        """10 HCP without Rule of 20 doesn't open."""
        # AKJ52=8, Q73=2, 843=0, 73=0 → 10 HCP, 5-3-3-2
        # R20=10+5+3=18<20
        ctx = _ctx("AKJ52.Q73.843.73")
        assert not self.rule.applies(ctx)

    def test_rule_of_20_opens(self):
        """Rule of 20 met: opens 1-major even below 12 HCP."""
        # AKJ52=8, KT73=3, 84=0, 73=0 → 11 HCP, 5-4-2-2
        # R20=11+5+4=20 ✓
        ctx = _ctx("AKJ52.KT73.84.73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1S"


# ── Open1Minor ───────────────────────────────────────────────────────


class TestOpen1Minor:
    rule = Open1Minor()

    def test_longer_diamonds(self):
        """Longer minor wins."""
        # K873=3, A2=4, KJ84=4, Q73=2 → 13 HCP, 4-2-4-3
        ctx = _ctx("K873.A2.KJ84.Q73")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_longer_clubs(self):
        """Longer minor wins."""
        # K873=3, A2=4, Q73=2, KJ84=4 → 13 HCP, 4-2-3-4
        ctx = _ctx("K873.A2.Q73.KJ84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1C"

    def test_4_4_minors_opens_1d(self):
        """SAYC: 4-4 in minors opens 1D."""
        # K97=3, A2=4, QJ84=3, K742=3 → 13 HCP, 3-2-4-4
        ctx = _ctx("K97.A2.QJ84.K742")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_3_3_minors_opens_1c(self):
        """SAYC: 3-3 in minors opens 1C."""
        # K873=3, K92=3, KJ8=4, A84=4 → 14 HCP, 4-3-3-3
        ctx = _ctx("K873.K92.KJ8.A84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1C"

    def test_4441_singleton_heart(self):
        """4-4-4-1 singleton heart: open 1D (4-4 in minors)."""
        # AK83=7, 9=0, AJ84=5, 9742=0 → 12 HCP, 4-1-4-4
        ctx = _ctx("AK83.9.AJ84.9742")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_4441_singleton_spade(self):
        """4-4-4-1 singleton spade: open 1D (4-4 in minors).

        The "middle suit" teaching aid suggests 1H, but that violates
        five-card majors. SAYC rules give 1D via 4-4 minors rule.
        """
        # 9=0, AK83=7, AJ84=5, 9742=0 → 12 HCP, 1-4-4-4
        ctx = _ctx("9.AK83.AJ84.9742")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_4441_singleton_diamond(self):
        """4-4-4-1 singleton diamond: open 1C (only 4 clubs in minors)."""
        # AK83=7, AJ84=5, 9=0, 9742=0 → 12 HCP, 4-4-1-4
        ctx = _ctx("AK83.AJ84.9.9742")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1C"

    def test_4441_singleton_club(self):
        """4-4-4-1 singleton club: open 1D (4 diamonds > 1 club)."""
        # AK83=7, AJ84=5, 9742=0, 9=0 → 12 HCP, 4-4-4-1
        ctx = _ctx("AK83.AJ84.9742.9")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"

    def test_has_5_card_major_rejected(self):
        """With a 5+ card major, 1-minor doesn't apply."""
        # AKJ52=8, Q73=2, 84=0, A73=4 → 14 HCP, 5-3-2-3
        ctx = _ctx("AKJ52.Q73.84.A73")
        assert not self.rule.applies(ctx)

    def test_balanced_15_17_rejected(self):
        """15-17 balanced opens 1NT, not 1-minor."""
        # AQ32=6, KJ8=4, Q84=2, K73=3 → 15 HCP, 4-3-3-3 balanced
        ctx = _ctx("AQ32.KJ8.Q84.K73")
        assert not self.rule.applies(ctx)

    def test_18_hcp_unbalanced_opens_minor(self):
        """18 HCP unbalanced with no 5-card major: opens 1-minor."""
        # AKQ3=9, KJ8=4, AJ832=5, 4=0 → 18 HCP, 4-3-5-1 (not balanced)
        ctx = _ctx("AKQ3.KJ8.AJ832.4")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "1D"


# ── OpenPass ─────────────────────────────────────────────────────────


class TestOpenPass:
    rule = OpenPass()

    def test_always_applies(self):
        """Pass is the fallback — always applies."""
        # 8432=0, 732=0, 843=0, J84=1 → 1 HCP
        ctx = _ctx("8432.732.843.J84")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)
        assert result.rule_name == "opening.pass"

    def test_does_not_apply_to_opening_strength(self):
        """A hand with opening strength should not match OpenPass."""
        ctx = _ctx("AKQJ.AKQ.AJ8.A84")
        assert not self.rule.applies(ctx)


# ── Seat-dependent opening strength ─────────────────────────────────


class TestSeatPosition:
    """Verify Rule of 20 / Rule of 15 seat-dependent behavior."""

    major_rule = Open1Major()
    minor_rule = Open1Minor()

    def test_rule_of_20_first_seat(self):
        """1st seat: Rule of 20 applies."""
        # AKJ52=8, KT73=3, 84=0, 73=0 → 11 HCP, 5-4-2-2
        # R20=11+5+4=20 ✓
        ctx = _ctx("AKJ52.KT73.84.73", seat=Seat.NORTH, dealer=Seat.NORTH)
        assert self.major_rule.applies(ctx)

    def test_rule_of_20_second_seat(self):
        """2nd seat: Rule of 20 applies."""
        ctx = _ctx("AKJ52.KT73.84.73", seat=Seat.EAST, dealer=Seat.NORTH)
        assert self.major_rule.applies(ctx)

    def test_rule_of_20_third_seat(self):
        """3rd seat: Rule of 20 applies (light openings)."""
        ctx = _ctx("AKJ52.KT73.84.73", seat=Seat.SOUTH, dealer=Seat.NORTH)
        assert self.major_rule.applies(ctx)

    def test_rule_of_15_fourth_seat_opens(self):
        """4th seat: Rule of 15 = 11 + 5 spades = 16 >= 15, opens."""
        # Same hand as above, but 4th seat uses R15
        ctx = _ctx("AKJ52.KT73.84.73", seat=Seat.WEST, dealer=Seat.NORTH)
        assert self.major_rule.applies(ctx)

    def test_rule_of_15_fourth_seat_fails(self):
        """4th seat: 10 HCP + 2 spades = 12 < 15, passes."""
        # 84=0, AKJ52=8, Q973=2, 73=0 → 10 HCP, 2-5-4-2
        # R15=10+2=12<15
        ctx = _ctx("84.AKJ52.Q973.73", seat=Seat.WEST, dealer=Seat.NORTH)
        assert not self.major_rule.applies(ctx)

    def test_rule_of_15_fourth_seat_minor_fails(self):
        """4th seat minor: 12 HCP + 2 spades = 14 < 15, passes."""
        # Q4=2, A93=4, KJ84=4, Q873=2 → 12 HCP, 2-3-4-4
        # R15=12+2=14<15
        ctx = _ctx("Q4.A93.KJ84.Q873", seat=Seat.WEST, dealer=Seat.NORTH)
        assert not self.minor_rule.applies(ctx)

    def test_rule_of_15_fourth_seat_minor_opens(self):
        """4th seat minor: 12 HCP + 4 spades = 16 >= 15, opens."""
        # KJ43=4, A9=4, KJ84=4, 873=0 → 12 HCP, 4-2-4-3
        # R15=12+4=16 ✓
        ctx = _ctx("KJ43.A9.KJ84.873", seat=Seat.WEST, dealer=Seat.NORTH)
        assert self.minor_rule.applies(ctx)
