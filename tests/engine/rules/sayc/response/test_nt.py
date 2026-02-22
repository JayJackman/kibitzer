"""Tests for responses to 1NT opening -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.response.nt import (
    Respond2NTOver1NT,
    Respond2SPuppet,
    Respond3MajorOver1NT,
    Respond3MinorOver1NT,
    Respond3NTOver1NT,
    Respond4NTOver1NT,
    RespondGerber,
    RespondJacobyTransfer,
    RespondPassOver1NT,
    RespondStayman,
    RespondTexasTransfer,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, is_pass, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str) -> BiddingContext:
    """Build a BiddingContext where partner opened 1NT and responder acts.

    North opens 1NT, East passes, South (responder) acts.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("1NT"))  # Partner (N) opens 1NT
    auction.add_bid(PASS)  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# ── RespondGerber ──────────────────────────────────────────────────


class TestRespondGerber:
    rule = RespondGerber()

    def test_18_hcp_balanced_no_5_major(self) -> None:
        """18+ HCP, balanced, no 5+ major -> 4C Gerber."""
        # AKQ3.AJ4.KQ3.K42 = 22 HCP, 4-3-3-3 balanced
        ctx = _ctx("AKQ3.AJ4.KQ3.K42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"

    def test_18_hcp_with_5_major_rejected(self) -> None:
        """18+ HCP but 5+ major -> should transfer, not Gerber."""
        # AKQJ3.A4.KQ3.K42 = 22 HCP, 5-2-3-3
        ctx = _ctx("AKQJ3.A4.KQ3.K42")
        assert not self.rule.applies(ctx)

    def test_17_hcp_rejected(self) -> None:
        """17 HCP -> quantitative 4NT, not Gerber."""
        # AK3.KJ4.KJ3.Q432 = 17 HCP, 3-3-3-4 balanced
        ctx = _ctx("AK3.KJ4.KJ3.Q432")
        assert not self.rule.applies(ctx)

    def test_18_hcp_semi_balanced(self) -> None:
        """18 HCP, semi-balanced (5-4-2-2) -> Gerber applies."""
        # AKQ3.AJ42.KQ3.K4 = 19 HCP, 4-4-3-2
        ctx = _ctx("AKQ3.AJ42.KQ3.K4")
        assert self.rule.applies(ctx)


# ── Respond4NTOver1NT ──────────────────────────────────────────────


class TestRespond4NTOver1NT:
    rule = Respond4NTOver1NT()

    def test_16_hcp_balanced(self) -> None:
        """15-17 HCP, balanced -> 4NT quantitative."""
        # AK3.KJ4.KJ3.Q432 = 17 HCP, 3-3-3-4 balanced
        ctx = _ctx("AK3.KJ4.KJ3.Q432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4NT"

    def test_14_hcp_rejected(self) -> None:
        """14 HCP -> not enough for 4NT."""
        # AK43.Q42.K43.542 = 13 HCP
        ctx = _ctx("AK43.Q42.K43.542")
        assert not self.rule.applies(ctx)

    def test_18_hcp_rejected(self) -> None:
        """18+ HCP -> Gerber instead."""
        # AKQ3.AJ4.KQ3.K42 = 22 HCP
        ctx = _ctx("AKQ3.AJ4.KQ3.K42")
        assert not self.rule.applies(ctx)


# ── Respond3MajorOver1NT ──────────────────────────────────────────


class TestRespond3MajorOver1NT:
    rule = Respond3MajorOver1NT()

    def test_6_hearts_16_hcp(self) -> None:
        """6+ hearts, 16+ HCP -> 3H slam interest."""
        # A4.AKQ932.KQ3.42 = 19 HCP, 2-6-3-2
        ctx = _ctx("A4.AKQ932.KQ3.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"
        assert result.forcing

    def test_6_spades_16_hcp(self) -> None:
        """6+ spades, 16+ HCP -> 3S slam interest."""
        # AKQ932.A4.KQ3.42 = 19 HCP, 6-2-3-2
        ctx = _ctx("AKQ932.A4.KQ3.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_5_hearts_rejected(self) -> None:
        """Only 5 hearts -> transfer, not 3H."""
        # A4.AKQ93.KQ3.432 = 18 HCP, 2-5-3-3
        ctx = _ctx("A4.AKQ93.KQ3.432")
        assert not self.rule.applies(ctx)

    def test_6_hearts_15_hcp_rejected(self) -> None:
        """6 hearts but only 15 HCP -> Texas, not 3H."""
        # 43.AKQ932.K43.42 = 13 HCP
        ctx = _ctx("43.AKQ932.K43.42")
        assert not self.rule.applies(ctx)


# ── RespondTexasTransfer ──────────────────────────────────────────


class TestRespondTexasTransfer:
    rule = RespondTexasTransfer()

    def test_6_hearts_10_hcp(self) -> None:
        """6+ hearts, 10-15 HCP -> 4D Texas transfer to hearts."""
        # K4.AQJ932.K43.42 = 13 HCP, 2-6-3-2
        ctx = _ctx("K4.AQJ932.K43.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"

    def test_6_spades_12_hcp(self) -> None:
        """6+ spades, 10-15 HCP -> 4H Texas transfer to spades."""
        # AQJ932.K4.K43.42 = 13 HCP, 6-2-3-2
        ctx = _ctx("AQJ932.K4.K43.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_6_hearts_9_hcp_rejected(self) -> None:
        """6 hearts but 9 HCP -> Jacoby transfer, not Texas."""
        # 43.KQJ932.K43.42 = 9 HCP
        ctx = _ctx("43.KQJ932.K43.42")
        assert not self.rule.applies(ctx)

    def test_6_hearts_16_hcp_rejected(self) -> None:
        """6 hearts, 16+ HCP -> 3M slam interest, not Texas."""
        # A4.AKQ932.KQ3.42 = 19 HCP
        ctx = _ctx("A4.AKQ932.KQ3.42")
        assert not self.rule.applies(ctx)


# ── RespondStayman ─────────────────────────────────────────────────


class TestRespondStayman:
    rule = RespondStayman()

    def test_4_hearts_10_hcp(self) -> None:
        """4 hearts, 10 HCP, not 4-3-3-3 -> Stayman 2C."""
        # KJ43.AQ42.K43.42 = 12 HCP, 4-4-3-2
        ctx = _ctx("KJ43.AQ42.K43.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"

    def test_4_hearts_4333_rejected(self) -> None:
        """4 hearts but 4-3-3-3 flat -> bid NT directly, not Stayman."""
        # KJ4.AQ42.K43.432 = 12 HCP, 3-4-3-3
        ctx = _ctx("KJ4.AQ42.K43.432")
        assert not self.rule.applies(ctx)

    def test_5_hearts_rejected(self) -> None:
        """5+ hearts -> Jacoby transfer, not Stayman."""
        # K43.AQ432.K43.42 = 12 HCP, 3-5-3-2
        ctx = _ctx("K43.AQ432.K43.42")
        assert not self.rule.applies(ctx)

    def test_garbage_stayman_4_4_majors(self) -> None:
        """4-4 in majors, weak hand -> garbage Stayman."""
        # J432.Q432.43.432 = 3 HCP, 4-4-2-3
        ctx = _ctx("J432.Q432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2C"

    def test_7_hcp_no_garbage_stayman(self) -> None:
        """7 HCP, only 4 hearts (not 4-4 majors) -> no Stayman."""
        # K43.QJ42.K43.432 = 7 HCP, 3-4-3-3
        ctx = _ctx("K43.QJ42.K43.432")
        assert not self.rule.applies(ctx)


# ── RespondJacobyTransfer ──────────────────────────────────────────


class TestRespondJacobyTransfer:
    rule = RespondJacobyTransfer()

    def test_5_hearts_any_hcp(self) -> None:
        """5+ hearts -> 2D Jacoby transfer."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx("432.KJ432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_5_spades_any_hcp(self) -> None:
        """5+ spades -> 2H Jacoby transfer."""
        # KJ432.432.43.432 = 4 HCP, 5-3-2-3
        ctx = _ctx("KJ432.432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_5_5_majors_transfers_to_spades(self) -> None:
        """5-5 in majors, equal length -> transfer to spades."""
        # KJ432.QJ432.4.43 = 6 HCP, 5-5-1-2
        ctx = _ctx("KJ432.QJ432.4.43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_6_hearts_5_spades_transfers_to_hearts(self) -> None:
        """6 hearts > 5 spades -> transfer to hearts."""
        # KJ432.QJ5432.4.3 = 7 HCP, 5-6-1-1
        ctx = _ctx("KJ432.QJ5432.4.3")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_0_hcp_signoff(self) -> None:
        """0 HCP with 5 hearts -> still transfers (sign-off)."""
        # 432.98765.43.432 = 0 HCP
        ctx = _ctx("432.98765.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_4_hearts_rejected(self) -> None:
        """Only 4 hearts -> Stayman, not transfer."""
        # K432.Q432.43.432 = 4 HCP
        ctx = _ctx("K432.Q432.43.432")
        assert not self.rule.applies(ctx)


# ── Respond3NTOver1NT ──────────────────────────────────────────────


class TestRespond3NTOver1NT:
    rule = Respond3NTOver1NT()

    def test_10_hcp_balanced(self) -> None:
        """10 HCP, balanced -> 3NT to play."""
        # KJ4.Q42.KJ3.Q432 = 11 HCP, 3-3-3-4
        ctx = _ctx("KJ4.Q42.KJ3.Q432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_9_hcp_rejected(self) -> None:
        """9 HCP -> 2NT invite, not 3NT."""
        # KJ4.Q42.J43.Q432 = 9 HCP
        ctx = _ctx("KJ4.Q42.J43.Q432")
        assert not self.rule.applies(ctx)

    def test_16_hcp_rejected(self) -> None:
        """16+ HCP -> higher-priority slam bids."""
        # AKQ3.KJ4.Q43.K42 = 17 HCP
        ctx = _ctx("AKQ3.KJ4.Q43.K42")
        assert not self.rule.applies(ctx)


# ── Respond3MinorOver1NT ──────────────────────────────────────────


class TestRespond3MinorOver1NT:
    rule = Respond3MinorOver1NT()

    def test_6_clubs_8_hcp(self) -> None:
        """6+ clubs, 8-9 HCP -> 3C invitational."""
        # Q43.K2.43.QJ8432 = 8 HCP, 3-2-2-6
        ctx = _ctx("Q43.K2.43.QJ8432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_6_diamonds_9_hcp(self) -> None:
        """6+ diamonds, 8-9 HCP -> 3D invitational."""
        # Q43.K2.QJ8432.43 = 8 HCP, 3-2-6-2
        ctx = _ctx("Q43.K2.QJ8432.43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_5_clubs_rejected(self) -> None:
        """Only 5 clubs -> no 3m invite."""
        # K43.42.432.AQJ43 = 9 HCP, 3-2-3-5
        ctx = _ctx("K43.42.432.AQJ43")
        assert not self.rule.applies(ctx)

    def test_10_hcp_rejected(self) -> None:
        """10 HCP with 6 clubs -> 3NT, not 3m."""
        # K43.K2.43.AQJ432 = 11 HCP
        ctx = _ctx("K43.K2.43.AQJ432")
        assert not self.rule.applies(ctx)


# ── Respond2NTOver1NT ──────────────────────────────────────────────


class TestRespond2NTOver1NT:
    rule = Respond2NTOver1NT()

    def test_8_hcp_balanced(self) -> None:
        """8-9 HCP -> 2NT invitational."""
        # K43.QJ4.J43.Q432 = 9 HCP, 3-3-3-4
        ctx = _ctx("K43.QJ4.J43.Q432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2NT"

    def test_7_hcp_rejected(self) -> None:
        """7 HCP -> pass, not invite."""
        # K43.J42.J43.Q432 = 7 HCP
        ctx = _ctx("K43.J42.J43.Q432")
        assert not self.rule.applies(ctx)

    def test_10_hcp_rejected(self) -> None:
        """10 HCP -> 3NT, not 2NT."""
        # K43.QJ4.KJ3.Q432 = 12 HCP
        ctx = _ctx("K43.QJ4.KJ3.Q432")
        assert not self.rule.applies(ctx)


# ── Respond2SPuppet ────────────────────────────────────────────────


class TestRespond2SPuppet:
    rule = Respond2SPuppet()

    def test_6_clubs_weak(self) -> None:
        """6+ clubs, 0-7 HCP -> 2S puppet."""
        # 432.43.43.QJ8432 = 3 HCP, 3-2-2-6
        ctx = _ctx("432.43.43.QJ8432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_6_diamonds_weak(self) -> None:
        """6+ diamonds, 0-7 HCP -> 2S puppet."""
        # 432.43.QJ8432.43 = 3 HCP, 3-2-6-2
        ctx = _ctx("432.43.QJ8432.43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_8_hcp_rejected(self) -> None:
        """8 HCP with 6 clubs -> 3m invite, not puppet."""
        # K43.42.43.AQJ432 = 9 HCP
        ctx = _ctx("K43.42.43.AQJ432")
        assert not self.rule.applies(ctx)

    def test_5_clubs_rejected(self) -> None:
        """Only 5 clubs -> pass, not puppet."""
        # 432.43.432.QJ843 = 3 HCP, 3-2-3-5
        ctx = _ctx("432.43.432.QJ843")
        assert not self.rule.applies(ctx)


# ── RespondPassOver1NT ─────────────────────────────────────────────


class TestRespondPassOver1NT:
    rule = RespondPassOver1NT()

    def test_weak_flat_hand(self) -> None:
        """0-7 HCP, no 5+ major, no 6+ minor, no 4-4 majors -> pass."""
        # 432.J42.J43.5432 = 2 HCP, 3-3-3-4
        ctx = _ctx("432.J42.J43.5432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)

    def test_8_hcp_rejected(self) -> None:
        """8 HCP -> not passing."""
        # K43.QJ4.J43.Q432 = 9 HCP
        ctx = _ctx("K43.QJ4.J43.Q432")
        assert not self.rule.applies(ctx)

    def test_not_over_1_suit(self) -> None:
        """Pass rule does not apply over 1H opening."""
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        ctx = BiddingContext(
            Board(
                hand=Hand.from_pbn("432.J42.J43.5432"),
                seat=Seat.SOUTH,
                auction=auction,
            )
        )
        assert not self.rule.applies(ctx)


# ── Priority conflict tests ────────────────────────────────────────


class TestPriorityConflicts:
    """Verify that the highest-priority applicable rule wins."""

    def test_5_hearts_10_hcp_transfer_over_3nt(self) -> None:
        """5H, 10 HCP -> Transfer (435) wins over 3NT (425)."""
        # K43.AQ432.K43.42 = 12 HCP, 3-5-3-2
        ctx = _ctx("K43.AQ432.K43.42")
        assert RespondJacobyTransfer().applies(ctx)
        assert Respond3NTOver1NT().applies(ctx)
        # Transfer has higher priority

    def test_6_hearts_10_hcp_texas_over_transfer(self) -> None:
        """6H, 10 HCP -> Texas (465) wins over Transfer (435)."""
        # K4.AQJ932.K43.42 = 13 HCP, 2-6-3-2
        ctx = _ctx("K4.AQJ932.K43.42")
        assert RespondTexasTransfer().applies(ctx)
        assert RespondJacobyTransfer().applies(ctx)

    def test_4_hearts_10_hcp_stayman_over_3nt(self) -> None:
        """4H non-flat, 10 HCP -> Stayman (445) wins over 3NT (425)."""
        # KJ43.AQ42.K43.42 = 12 HCP, 4-4-3-2
        ctx = _ctx("KJ43.AQ42.K43.42")
        assert RespondStayman().applies(ctx)
        assert Respond3NTOver1NT().applies(ctx)

    def test_4_hearts_4333_10_hcp_3nt_only(self) -> None:
        """4H 4-3-3-3, 10 HCP -> only 3NT applies (not Stayman)."""
        # KJ4.AQ42.K43.432 = 12 HCP, 3-4-3-3
        ctx = _ctx("KJ4.AQ42.K43.432")
        assert not RespondStayman().applies(ctx)
        assert Respond3NTOver1NT().applies(ctx)

    def test_garbage_stayman_over_pass(self) -> None:
        """4-4 majors, weak -> Stayman (445) wins over Pass (45)."""
        # J432.Q432.43.432 = 3 HCP, 4-4-2-3
        ctx = _ctx("J432.Q432.43.432")
        assert RespondStayman().applies(ctx)
        assert RespondPassOver1NT().applies(ctx)

    def test_5_hearts_0_hcp_transfer_over_pass(self) -> None:
        """5H, 0 HCP -> Transfer (435) wins over Pass (45)."""
        # 432.98765.43.432 = 0 HCP
        ctx = _ctx("432.98765.43.432")
        assert RespondJacobyTransfer().applies(ctx)
        assert RespondPassOver1NT().applies(ctx)
