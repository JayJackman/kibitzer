"""Tests for responses to 1NT and 2NT openings -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.response.nt import (
    Respond2NTOver1NT,
    Respond2SPuppet,
    Respond3MajorOver1NT,
    Respond3MinorOver1NT,
    Respond3NTOver1NT,
    Respond3NTOver2NT,
    Respond3SPuppetOver2NT,
    Respond4NTOver1NT,
    Respond4NTOver2NT,
    RespondGerber,
    RespondGerberOver2NT,
    RespondJacobyTransferHearts,
    RespondJacobyTransferSpades,
    RespondPassOver1NT,
    RespondPassOver2NT,
    RespondStayman,
    RespondStaymanOver2NT,
    RespondTexasOver2NT,
    RespondTexasTransfer,
    RespondTransferHeartsOver2NT,
    RespondTransferSpadesOver2NT,
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


# ── RespondJacobyTransferHearts ────────────────────────────────────


class TestRespondJacobyTransferHearts:
    rule = RespondJacobyTransferHearts()

    def test_5_hearts_any_hcp(self) -> None:
        """5+ hearts -> 2D Jacoby transfer."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx("432.KJ432.43.432")
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

    def test_6_hearts_5_spades_transfers_to_hearts(self) -> None:
        """6 hearts > 5 spades -> hearts rule matches."""
        # KJ432.QJ5432.4.3 = 7 HCP, 5-6-1-1
        ctx = _ctx("KJ432.QJ5432.4.3")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_4_hearts_rejected(self) -> None:
        """Only 4 hearts -> not enough for transfer."""
        # K432.Q432.43.432 = 4 HCP
        ctx = _ctx("K432.Q432.43.432")
        assert not self.rule.applies(ctx)

    def test_5_spades_no_hearts_rejected(self) -> None:
        """5 spades but only 3 hearts -> hearts rule doesn't apply."""
        # KJ432.432.43.432 = 4 HCP, 5-3-2-3
        ctx = _ctx("KJ432.432.43.432")
        assert not self.rule.applies(ctx)


# ── RespondJacobyTransferSpades ───────────────────────────────────


class TestRespondJacobyTransferSpades:
    rule = RespondJacobyTransferSpades()

    def test_5_spades_any_hcp(self) -> None:
        """5+ spades -> 2H Jacoby transfer."""
        # KJ432.432.43.432 = 4 HCP, 5-3-2-3
        ctx = _ctx("KJ432.432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_5_5_majors_both_rules_match(self) -> None:
        """5-5 in majors -> spades rule matches too."""
        # KJ432.QJ432.4.43 = 6 HCP, 5-5-1-2
        ctx = _ctx("KJ432.QJ432.4.43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_4_spades_rejected(self) -> None:
        """Only 4 spades -> not enough for transfer."""
        # K432.Q432.43.432 = 4 HCP
        ctx = _ctx("K432.Q432.43.432")
        assert not self.rule.applies(ctx)

    def test_5_hearts_no_spades_rejected(self) -> None:
        """5 hearts but only 3 spades -> spades rule doesn't apply."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx("432.KJ432.43.432")
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
        assert RespondJacobyTransferHearts().applies(ctx)
        assert Respond3NTOver1NT().applies(ctx)
        # Transfer has higher priority

    def test_6_hearts_10_hcp_texas_over_transfer(self) -> None:
        """6H, 10 HCP -> Texas (465) wins over Transfer (435)."""
        # K4.AQJ932.K43.42 = 13 HCP, 2-6-3-2
        ctx = _ctx("K4.AQJ932.K43.42")
        assert RespondTexasTransfer().applies(ctx)
        assert RespondJacobyTransferHearts().applies(ctx)

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
        assert RespondJacobyTransferHearts().applies(ctx)
        assert RespondPassOver1NT().applies(ctx)


# ══════════════════════════════════════════════════════════════════════
# Responses to 2NT opening
# ══════════════════════════════════════════════════════════════════════


def _ctx_2nt(pbn: str) -> BiddingContext:
    """Build a BiddingContext where partner opened 2NT and responder acts.

    North opens 2NT, East passes, South (responder) acts.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("2NT"))  # Partner (N) opens 2NT
    auction.add_bid(PASS)  # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )


# ── RespondGerberOver2NT ──────────────────────────────────────────


class TestRespondGerberOver2NT:
    rule = RespondGerberOver2NT()

    def test_13_hcp_balanced_no_5_major(self) -> None:
        """13+ HCP, balanced, no 5+ major -> 4C Gerber."""
        # AQ3.KJ4.KQ3.Q432 = 16 HCP, 3-3-3-4 balanced
        ctx = _ctx_2nt("AQ3.KJ4.KQ3.Q432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"

    def test_13_hcp_with_5_major_rejected(self) -> None:
        """13+ HCP but 5+ major -> should transfer, not Gerber."""
        # AKQ43.A4.KQ3.432 = 18 HCP, 5-2-3-3
        ctx = _ctx_2nt("AKQ43.A4.KQ3.432")
        assert not self.rule.applies(ctx)

    def test_12_hcp_rejected(self) -> None:
        """12 HCP -> quantitative 4NT, not Gerber."""
        # KJ3.Q42.KJ3.Q432 = 12 HCP, 3-3-3-4
        ctx = _ctx_2nt("KJ3.Q42.KJ3.Q432")
        assert not self.rule.applies(ctx)

    def test_not_over_1nt(self) -> None:
        """Gerber over 2NT does not apply over 1NT opening."""
        ctx = _ctx("AQ3.KJ4.KQ3.Q432")
        assert not self.rule.applies(ctx)


# ── Respond4NTOver2NT ─────────────────────────────────────────────


class TestRespond4NTOver2NT:
    rule = Respond4NTOver2NT()

    def test_11_hcp_balanced(self) -> None:
        """11-12 HCP, balanced -> 4NT quantitative."""
        # AQ3.K42.J43.Q432 = 12 HCP, 3-3-3-4
        ctx = _ctx_2nt("AQ3.K42.J43.Q432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4NT"

    def test_10_hcp_rejected(self) -> None:
        """10 HCP -> 3NT, not 4NT."""
        # KJ4.Q42.J43.Q432 = 9 HCP
        ctx = _ctx_2nt("KJ4.Q42.J43.Q432")
        assert not self.rule.applies(ctx)

    def test_13_hcp_rejected(self) -> None:
        """13+ HCP -> Gerber, not 4NT."""
        # AQ3.KJ4.KQ3.Q432 = 16 HCP
        ctx = _ctx_2nt("AQ3.KJ4.KQ3.Q432")
        assert not self.rule.applies(ctx)


# ── RespondTexasOver2NT ───────────────────────────────────────────


class TestRespondTexasOver2NT:
    rule = RespondTexasOver2NT()

    def test_6_hearts_8_hcp(self) -> None:
        """6+ hearts, 4-10 HCP -> 4D Texas transfer."""
        # 43.KQJ932.Q43.42 = 8 HCP, 2-6-3-2
        ctx = _ctx_2nt("43.KQJ932.Q43.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"

    def test_6_spades_5_hcp(self) -> None:
        """6+ spades, 4-10 HCP -> 4H Texas transfer."""
        # KJ9432.43.Q43.42 = 6 HCP, 6-2-3-2
        ctx = _ctx_2nt("KJ9432.43.Q43.42")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_3_hcp_rejected(self) -> None:
        """3 HCP with 6 hearts -> transfer (not Texas), too weak for game."""
        # 43.J98432.Q43.42 = 3 HCP
        ctx = _ctx_2nt("43.J98432.Q43.42")
        assert not self.rule.applies(ctx)

    def test_11_hcp_rejected(self) -> None:
        """11 HCP with 6 hearts -> slam interest, not Texas."""
        # A4.AQJ932.Q43.42 = 13 HCP
        ctx = _ctx_2nt("A4.AQJ932.Q43.42")
        assert not self.rule.applies(ctx)


# ── RespondStaymanOver2NT ─────────────────────────────────────────


class TestRespondStaymanOver2NT:
    rule = RespondStaymanOver2NT()

    def test_4_hearts_5_hcp(self) -> None:
        """4 hearts, 5 HCP, not 4-3-3-3 -> Stayman 3C."""
        # Q432.QJ42.43.432 = 4 HCP, 4-4-2-3
        ctx = _ctx_2nt("Q432.QJ42.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_4_hearts_4333_rejected(self) -> None:
        """4 hearts but 4-3-3-3 flat -> bid 3NT directly."""
        # Q42.QJ42.432.432 = 4 HCP, 3-4-3-3
        ctx = _ctx_2nt("Q42.QJ42.432.432")
        assert not self.rule.applies(ctx)

    def test_5_hearts_rejected(self) -> None:
        """5+ hearts -> transfer, not Stayman."""
        # Q43.QJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx_2nt("Q43.QJ432.43.432")
        assert not self.rule.applies(ctx)

    def test_3_hcp_rejected(self) -> None:
        """3 HCP with 4-card major -> too weak for Stayman over 2NT."""
        # J432.J432.43.432 = 2 HCP
        ctx = _ctx_2nt("J432.J432.43.432")
        assert not self.rule.applies(ctx)

    def test_no_garbage_stayman_over_2nt(self) -> None:
        """4-4 majors, 2 HCP -> no garbage Stayman over 2NT (unlike 1NT)."""
        # J432.Q432.43.432 = 3 HCP, 4-4-2-3
        ctx = _ctx_2nt("J432.Q432.43.432")
        assert not self.rule.applies(ctx)


# ── RespondTransferHeartsOver2NT ──────────────────────────────────


class TestRespondTransferHeartsOver2NT:
    rule = RespondTransferHeartsOver2NT()

    def test_5_hearts_any_hcp(self) -> None:
        """5+ hearts -> 3D transfer."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx_2nt("432.KJ432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_0_hcp_signoff(self) -> None:
        """0 HCP with 5 hearts -> still transfers (sign-off at 3H)."""
        # 432.98765.43.432 = 0 HCP
        ctx = _ctx_2nt("432.98765.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_4_hearts_rejected(self) -> None:
        """Only 4 hearts -> not enough for transfer."""
        # K432.Q432.43.432 = 4 HCP
        ctx = _ctx_2nt("K432.Q432.43.432")
        assert not self.rule.applies(ctx)

    def test_5_spades_no_hearts_rejected(self) -> None:
        """5 spades but only 3 hearts -> hearts rule doesn't apply."""
        # KJ432.432.43.432 = 4 HCP, 5-3-2-3
        ctx = _ctx_2nt("KJ432.432.43.432")
        assert not self.rule.applies(ctx)


# ── RespondTransferSpadesOver2NT ─────────────────────────────────


class TestRespondTransferSpadesOver2NT:
    rule = RespondTransferSpadesOver2NT()

    def test_5_spades_any_hcp(self) -> None:
        """5+ spades -> 3H transfer."""
        # KJ432.432.43.432 = 4 HCP, 5-3-2-3
        ctx = _ctx_2nt("KJ432.432.43.432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_4_spades_rejected(self) -> None:
        """Only 4 spades -> not enough for transfer."""
        # K432.Q432.43.432 = 4 HCP
        ctx = _ctx_2nt("K432.Q432.43.432")
        assert not self.rule.applies(ctx)

    def test_5_hearts_no_spades_rejected(self) -> None:
        """5 hearts but only 3 spades -> spades rule doesn't apply."""
        # 432.KJ432.43.432 = 4 HCP, 3-5-2-3
        ctx = _ctx_2nt("432.KJ432.43.432")
        assert not self.rule.applies(ctx)


# ── Respond3NTOver2NT ─────────────────────────────────────────────


class TestRespond3NTOver2NT:
    rule = Respond3NTOver2NT()

    def test_6_hcp_balanced(self) -> None:
        """4-10 HCP -> 3NT to play."""
        # Q43.J42.K43.J432 = 7 HCP, 3-3-3-4
        ctx = _ctx_2nt("Q43.J42.K43.J432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_3_hcp_rejected(self) -> None:
        """3 HCP -> pass, not 3NT."""
        # 432.J42.432.J432 = 2 HCP
        ctx = _ctx_2nt("432.J42.432.J432")
        assert not self.rule.applies(ctx)

    def test_11_hcp_rejected(self) -> None:
        """11 HCP -> quantitative 4NT, not 3NT."""
        # AQ3.K42.J43.Q432 = 12 HCP
        ctx = _ctx_2nt("AQ3.K42.J43.Q432")
        assert not self.rule.applies(ctx)


# ── Respond3SPuppetOver2NT ────────────────────────────────────────


class TestRespond3SPuppetOver2NT:
    rule = Respond3SPuppetOver2NT()

    def test_6_clubs_weak(self) -> None:
        """6+ clubs, 0-3 HCP -> 3S puppet."""
        # 432.43.43.J98432 = 1 HCP, 3-2-2-6
        ctx = _ctx_2nt("432.43.43.J98432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_6_diamonds_weak(self) -> None:
        """6+ diamonds, 0-3 HCP -> 3S puppet."""
        # 432.43.J98432.43 = 1 HCP, 3-2-6-2
        ctx = _ctx_2nt("432.43.J98432.43")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_4_hcp_rejected(self) -> None:
        """4 HCP with 6 clubs -> 3NT or Stayman, not puppet."""
        # Q32.42.43.QJ8432 = 5 HCP
        ctx = _ctx_2nt("Q32.42.43.QJ8432")
        assert not self.rule.applies(ctx)


# ── RespondPassOver2NT ────────────────────────────────────────────


class TestRespondPassOver2NT:
    rule = RespondPassOver2NT()

    def test_weak_flat_hand(self) -> None:
        """0-3 HCP, no 6+ minor -> pass."""
        # 432.J42.432.5432 = 1 HCP, 3-3-3-4
        ctx = _ctx_2nt("432.J42.432.5432")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)

    def test_4_hcp_rejected(self) -> None:
        """4 HCP -> game values over 2NT, not passing."""
        # K43.J42.J43.5432 = 4 HCP
        ctx = _ctx_2nt("K43.J42.J43.5432")
        assert not self.rule.applies(ctx)

    def test_not_over_1nt(self) -> None:
        """Pass over 2NT does not apply over 1NT opening."""
        ctx = _ctx("432.J42.432.5432")
        assert not self.rule.applies(ctx)


# ── 2NT Priority conflict tests ──────────────────────────────────


class TestPriorityConflicts2NT:
    """Verify priority ordering for 2NT responses."""

    def test_5_hearts_8_hcp_transfer_over_3nt(self) -> None:
        """5H, 8 HCP -> Transfer (434) wins over 3NT (424)."""
        ctx = _ctx_2nt("432.KJ432.K43.42")
        assert RespondTransferHeartsOver2NT().applies(ctx)
        assert Respond3NTOver2NT().applies(ctx)

    def test_6_hearts_8_hcp_texas_over_transfer(self) -> None:
        """6H, 8 HCP -> Texas (464) wins over Transfer (434)."""
        ctx = _ctx_2nt("43.KQJ932.Q43.42")
        assert RespondTexasOver2NT().applies(ctx)
        assert RespondTransferHeartsOver2NT().applies(ctx)

    def test_4_hearts_5_hcp_stayman_over_3nt(self) -> None:
        """4H non-flat, 5 HCP -> Stayman (444) wins over 3NT (424)."""
        ctx = _ctx_2nt("Q432.QJ42.43.432")
        assert RespondStaymanOver2NT().applies(ctx)
        assert Respond3NTOver2NT().applies(ctx)

    def test_6_clubs_2_hcp_puppet_over_pass(self) -> None:
        """6C, 2 HCP -> 3S puppet (394) wins over Pass (44)."""
        ctx = _ctx_2nt("432.43.43.J98432")
        assert Respond3SPuppetOver2NT().applies(ctx)
        assert RespondPassOver2NT().applies(ctx)
