"""Tests for responses to preemptive openings -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.response.preempt import (
    Respond2NTFeatureAsk,
    Respond3NTOver3Level,
    Respond3NTOverWeakTwo,
    RespondGameRaise3LevelMajor,
    RespondGameRaise3LevelMinor,
    RespondGameRaiseWeakTwoMajor,
    RespondGameRaiseWeakTwoMinor,
    RespondNewSuitOver3Level,
    RespondNewSuitOverWeakTwo,
    RespondPassOver3Level,
    RespondPassOver4Level,
    RespondPassOverWeakTwo,
    RespondRaise3Level,
    RespondRaise4Level,
    RespondRaiseWeakTwo,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str, opening: str) -> BiddingContext:
    """Build a BiddingContext where partner opened and responder acts.

    North opens, East passes, South (responder) acts.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))
    auction.add_bid(PASS)
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# ===========================================================================
# B4: Weak Two Responses
# ===========================================================================


class TestRespondGameRaiseWeakTwoMajor:
    rule = RespondGameRaiseWeakTwoMajor()

    def test_game_raise_major_with_values(self) -> None:
        """3+ support, 14+ support points -> 4H."""
        # 12 HCP, 4 hearts, singleton diamond = +3 -> 15 support points
        ctx = _ctx("K432.KQ43.4.A432", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_game_raise_preemptive_5_trumps(self) -> None:
        """5+ support in major, weak hand -> preemptive 4S."""
        # 2 HCP, 5 spades
        ctx = _ctx("Q5432.432.5432.5", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_2_card_support_rejected(self) -> None:
        """Only 2 cards in partner's suit -> no game raise."""
        # 15 HCP, 2 hearts
        ctx = _ctx("AK43.K4.Q432.K43", "2H")
        assert not self.rule.applies(ctx)


class TestRespondGameRaiseWeakTwoMinor:
    rule = RespondGameRaiseWeakTwoMinor()

    def test_game_raise_minor(self) -> None:
        """3+ support, 16+ support pts -> 5D."""
        # 13 HCP, 4 diamonds, singleton heart = +3 -> 16 support points
        ctx = _ctx("A432.4.Q432.AK32", "2D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "5D"

    def test_minor_insufficient_values_rejected(self) -> None:
        """3+ support in minor but <16 support points -> no game raise."""
        # 10 HCP, 3 diamonds, no shortness -> 10 support points
        ctx = _ctx("K43.Q43.Q43.K432", "2D")
        assert not self.rule.applies(ctx)

    def test_preemptive_not_for_minor(self) -> None:
        """5+ support in minor, weak -> no preemptive game (needs 16+ sp)."""
        # 2 HCP, 5 diamonds -> 2 + 3 (singleton) = 5 support points
        ctx = _ctx("5432.4.Q5432.432", "2D")
        assert not self.rule.applies(ctx)


class TestRespond3NTOverWeakTwo:
    rule = Respond3NTOverWeakTwo()

    def test_stoppers_and_values(self) -> None:
        """15+ HCP, stoppers in all unbid suits -> 3NT."""
        # 15 HCP; partner opened 2H; stoppers in S(A), D(AK), C(Q+3)
        ctx = _ctx("AQ43.43.AK32.Q43", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_no_stopper_rejected(self) -> None:
        """15+ HCP but missing stopper -> no 3NT."""
        # 16 HCP; partner opened 2H; no spade stopper (5432)
        ctx = _ctx("5432.43.AKQ3.AQ4", "2H")
        assert not self.rule.applies(ctx)

    def test_14_hcp_rejected(self) -> None:
        """14 HCP (below threshold) -> no 3NT."""
        # 14 HCP, stoppers present
        ctx = _ctx("AQ43.43.K432.Q43", "2H")
        assert not self.rule.applies(ctx)


class TestRespondNewSuitOverWeakTwo:
    rule = RespondNewSuitOverWeakTwo()

    def test_5_card_suit_higher(self) -> None:
        """5+ suit ranking higher -> bid at 2-level."""
        # 14 HCP, 5 spades; partner opened 2H
        ctx = _ctx("AKQ32.43.K43.Q43", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_5_card_suit_lower(self) -> None:
        """5+ suit ranking lower -> bid at 3-level."""
        # 14 HCP, 5 clubs; partner opened 2S
        ctx = _ctx("43.AK3.Q43.AJ432", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_13_hcp_rejected(self) -> None:
        """13 HCP -> not enough for new suit."""
        # 13 HCP, 5 spades
        ctx = _ctx("AK432.43.Q43.K43", "2H")
        assert not self.rule.applies(ctx)

    def test_no_5_card_suit_rejected(self) -> None:
        """No 5+ card suit -> no new suit bid."""
        # 15 HCP, no 5+ suit
        ctx = _ctx("AK43.43.KQ43.Q43", "2H")
        assert not self.rule.applies(ctx)


class TestRespond2NTFeatureAsk:
    rule = Respond2NTFeatureAsk()

    def test_14_hcp_game_interest(self) -> None:
        """14+ HCP -> 2NT feature ask."""
        # 14 HCP
        ctx = _ctx("K432.43.AQ43.AJ3", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_13_hcp_rejected(self) -> None:
        """13 HCP -> no feature ask."""
        ctx = _ctx("K432.43.Q432.AK3", "2H")
        assert not self.rule.applies(ctx)


class TestRespondRaiseWeakTwo:
    rule = RespondRaiseWeakTwo()

    def test_3_card_support(self) -> None:
        """3+ support -> preemptive raise."""
        # 7 HCP, 3 hearts
        ctx = _ctx("K432.Q43.5432.43", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_raise_spades(self) -> None:
        """3+ spade support -> 3S."""
        ctx = _ctx("Q43.K432.5432.43", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_2_card_support_rejected(self) -> None:
        """Only 2 support -> no raise."""
        ctx = _ctx("K432.43.5432.432", "2H")
        assert not self.rule.applies(ctx)


class TestRespondPassOverWeakTwo:
    rule = RespondPassOverWeakTwo()

    def test_applies_to_any_weak_two(self) -> None:
        """Pass always applies over weak two."""
        ctx = _ctx("5432.432.5432.43", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "Pass"

    def test_not_after_1nt(self) -> None:
        """Does not apply after 1NT opening."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1NT"))
        auction.add_bid(PASS)
        hand = Hand.from_pbn("5432.432.5432.43")
        ctx = BiddingContext(Board(hand=hand, seat=Seat.SOUTH, auction=auction))
        assert not self.rule.applies(ctx)


# ===========================================================================
# B5: 3-Level Preempt Responses
# ===========================================================================


class TestRespondGameRaise3LevelMajor:
    rule = RespondGameRaise3LevelMajor()

    def test_game_raise_major(self) -> None:
        """3+ support, 14+ support pts -> 4H over 3H."""
        # 12 HCP, 3 hearts, singleton diamond = +3 -> 15 support points
        ctx = _ctx("AK43.K43.4.Q5432", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_insufficient_values_rejected(self) -> None:
        """3 support but <14 support pts -> no game raise."""
        # 10 HCP, 3 hearts, no shortness
        ctx = _ctx("K43.Q43.Q43.K432", "3H")
        assert not self.rule.applies(ctx)


class TestRespondGameRaise3LevelMinor:
    rule = RespondGameRaise3LevelMinor()

    def test_game_raise_minor(self) -> None:
        """3+ support, 16+ support pts -> 5C over 3C."""
        # 15 HCP, 4 clubs, singleton heart = +3 -> 18 support points
        ctx = _ctx("AK43.4.A432.KJ32", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "5C"


class TestRespond3NTOver3Level:
    rule = Respond3NTOver3Level()

    def test_stoppers_over_3c(self) -> None:
        """15+ HCP, stoppers in S/H/D -> 3NT over 3C."""
        # 16 HCP, stoppers in S(A), H(K+3), D(AK)
        ctx = _ctx("AQ43.K43.AK32.43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_stoppers_over_3s(self) -> None:
        """15+ HCP, stoppers in C/D/H -> 3NT over 3S."""
        # 16 HCP, stoppers in H(A), D(K+4), C(AJ+3)
        ctx = _ctx("43.AQ43.KQ32.AJ3", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"


class TestRespondNewSuitOver3Level:
    rule = RespondNewSuitOver3Level()

    def test_higher_suit_over_3c(self) -> None:
        """5+ spades over 3C -> 3S."""
        # 14 HCP, 5 spades (higher than clubs)
        ctx = _ctx("AK432.Q43.AJ3.43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_3s_over_3h(self) -> None:
        """5+ spades over 3H -> 3S (only option)."""
        # 14 HCP, 5 spades
        ctx = _ctx("AK432.43.AJ3.Q43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_no_higher_suit_over_3s(self) -> None:
        """Over 3S, no higher suit possible at 3-level -> does not apply."""
        # 15 HCP, 5 hearts (lower than spades)
        ctx = _ctx("43.AK432.K43.Q43", "3S")
        assert not self.rule.applies(ctx)

    def test_lower_suit_rejected(self) -> None:
        """5+ clubs over 3D -> can't bid 3C (lower) -> does not apply."""
        # 14 HCP, 5 clubs but clubs < diamonds
        ctx = _ctx("K43.K43.43.AQJ32", "3D")
        assert not self.rule.applies(ctx)


class TestRespondRaise3Level:
    rule = RespondRaise3Level()

    def test_raise_3h_to_4h(self) -> None:
        """3+ support -> 4H."""
        ctx = _ctx("K432.Q43.5432.43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_raise_3c_to_4c(self) -> None:
        """3+ support -> 4C."""
        ctx = _ctx("K432.5432.43.Q43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"


class TestRespondPassOver3Level:
    rule = RespondPassOver3Level()

    def test_applies_to_3_level(self) -> None:
        """Pass always applies over 3-level preempt."""
        ctx = _ctx("5432.432.5432.43", "3H")
        assert self.rule.applies(ctx)


# ===========================================================================
# B6: 4-Level Preempt Responses
# ===========================================================================


class TestRespondRaise4Level:
    rule = RespondRaise4Level()

    def test_raise_4c_to_5c(self) -> None:
        """4+ support, 14+ sp over 4C -> 5C."""
        # 14 HCP, 4 clubs, singleton heart = +3 -> 17 support points
        ctx = _ctx("AK43.4.K432.Q432", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "5C"

    def test_raise_4d_to_5d(self) -> None:
        """4+ support, 14+ sp over 4D -> 5D."""
        # 14 HCP, 4 diamonds, singleton heart = +3 -> 17 support points
        ctx = _ctx("AK43.4.Q432.K432", "4D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "5D"

    def test_major_rejected(self) -> None:
        """Over 4H/4S -> does not raise (slam territory)."""
        ctx = _ctx("AK43.Q432.4.K432", "4H")
        assert not self.rule.applies(ctx)

    def test_insufficient_support_rejected(self) -> None:
        """Only 3 clubs -> no raise."""
        # 12 HCP, 3 clubs
        ctx = _ctx("AK43.K43.Q432.32", "4C")
        assert not self.rule.applies(ctx)


class TestRespondPassOver4Level:
    rule = RespondPassOver4Level()

    def test_applies_to_4_level(self) -> None:
        """Pass always applies over 4-level preempt."""
        ctx = _ctx("5432.432.5432.43", "4H")
        assert self.rule.applies(ctx)


# ===========================================================================
# Priority Conflicts
# ===========================================================================


class TestWeakTwoPriorityConflicts:
    """Verify priority ordering resolves ambiguities for weak two responses."""

    def test_game_raise_beats_3nt(self) -> None:
        """With fit and stoppers, game raise wins."""
        r_game = RespondGameRaiseWeakTwoMajor()
        r_3nt = Respond3NTOverWeakTwo()
        # 18 HCP, 4 hearts, doubleton D = +1 -> 19 sp; stoppers in S(A), D(A), C(Q+3)
        ctx = _ctx("AK43.KQ43.A4.Q32", "2H")
        assert r_game.applies(ctx)
        assert r_3nt.applies(ctx)
        assert r_game.priority > r_3nt.priority

    def test_3nt_beats_new_suit(self) -> None:
        """With stoppers, 3NT wins over new suit."""
        r_3nt = Respond3NTOverWeakTwo()
        r_new = RespondNewSuitOverWeakTwo()
        # 16 HCP, 5 spades, stoppers in S(A), D(A), C(K+3)
        ctx = _ctx("AK432.43.AQ3.K43", "2H")
        assert r_3nt.applies(ctx)
        assert r_new.applies(ctx)
        assert r_3nt.priority > r_new.priority

    def test_new_suit_beats_2nt(self) -> None:
        """With 5+ suit, new suit wins over 2NT ask."""
        r_new = RespondNewSuitOverWeakTwo()
        r_2nt = Respond2NTFeatureAsk()
        # 15 HCP, 5 spades, no club stopper (Qx)
        ctx = _ctx("AKJ32.43.KQ32.Q3", "2H")
        assert r_new.applies(ctx)
        assert r_2nt.applies(ctx)
        assert r_new.priority > r_2nt.priority

    def test_2nt_beats_raise(self) -> None:
        """With game interest, 2NT wins over preemptive raise."""
        r_2nt = Respond2NTFeatureAsk()
        r_raise = RespondRaiseWeakTwo()
        # 14 HCP, 3 hearts
        ctx = _ctx("K432.KQ4.AQ32.43", "2H")
        assert r_2nt.applies(ctx)
        assert r_raise.applies(ctx)
        assert r_2nt.priority > r_raise.priority

    def test_raise_beats_pass(self) -> None:
        """With support, raise wins over pass."""
        r_raise = RespondRaiseWeakTwo()
        r_pass = RespondPassOverWeakTwo()
        ctx = _ctx("K432.Q43.5432.43", "2H")
        assert r_raise.applies(ctx)
        assert r_pass.applies(ctx)
        assert r_raise.priority > r_pass.priority
