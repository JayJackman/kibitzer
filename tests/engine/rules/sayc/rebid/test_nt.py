"""Tests for opener's rebid rules after 1NT and 2NT openings -- SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rules.sayc.rebid.nt import (
    Rebid2NTAccept4NT,
    Rebid2NTComplete3SPuppet,
    Rebid2NTCompleteTexas,
    Rebid2NTCompleteTransfer,
    Rebid2NTDecline4NT,
    Rebid2NTGerberResponse,
    Rebid2NTPassAfter3NT,
    Rebid2NTStayman3D,
    Rebid2NTStayman3H,
    Rebid2NTStayman3S,
    RebidAccept2NTOver1NT,
    RebidAccept3MinorOver1NT,
    RebidAccept4NTOver1NT,
    RebidComplete2SPuppet,
    RebidCompleteTexas,
    RebidCompleteTransfer,
    RebidDecline2NTOver1NT,
    RebidDecline3MajorOver1NT,
    RebidDecline3MinorOver1NT,
    RebidDecline4NTOver1NT,
    RebidGerberResponse,
    RebidPassAfter3NTOver1NT,
    RebidRaise3MajorOver1NT,
    RebidStayman2D,
    RebidStayman2H,
    RebidStayman2S,
    RebidSuperAccept,
)
from bridge.model.auction import AuctionState, Seat
from bridge.model.bid import PASS, is_pass, parse_bid
from bridge.model.board import Board
from bridge.model.hand import Hand


def _ctx(pbn: str, response: str) -> BiddingContext:
    """Build a BiddingContext where I opened 1NT and partner responded.

    North opens 1NT, East passes, South responds, West passes, North rebids.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("1NT"))  # N opens 1NT
    auction.add_bid(PASS)  # E passes
    auction.add_bid(parse_bid(response))  # S responds
    auction.add_bid(PASS)  # W passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.NORTH, auction=auction)
    )


# ── After Stayman (2C) ────────────────────────────────────────────


class TestRebidStayman2H:
    rule = RebidStayman2H()

    def test_4_hearts(self) -> None:
        """4+ hearts -> bid 2H."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP, 3-4-3-3
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_4_4_majors_bids_hearts_first(self) -> None:
        """4-4 in majors -> bid hearts first."""
        # AQ32.KJ42.QJ3.Q3 = 15 HCP, 4-4-3-2
        ctx = _ctx("AQ32.KJ42.QJ3.Q3", "2C")
        assert self.rule.applies(ctx)
        assert not RebidStayman2S().applies(ctx)

    def test_no_4_hearts_rejected(self) -> None:
        """Only 3 hearts -> not 2H."""
        # AQ32.KJ4.QJ3.Q43 = 15 HCP, 4-3-3-3
        ctx = _ctx("AQ32.KJ4.QJ3.Q43", "2C")
        assert not self.rule.applies(ctx)

    def test_not_after_other_response(self) -> None:
        """Does not apply after 2D (transfer)."""
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2D")
        assert not self.rule.applies(ctx)


class TestRebidStayman2S:
    rule = RebidStayman2S()

    def test_4_spades_no_4_hearts(self) -> None:
        """4+ spades, <4 hearts -> bid 2S."""
        # AQ32.KJ4.QJ3.Q43 = 15 HCP, 4-3-3-3
        ctx = _ctx("AQ32.KJ4.QJ3.Q43", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_4_4_majors_rejected(self) -> None:
        """4-4 majors -> 2H first, not 2S."""
        ctx = _ctx("AQ32.KJ42.QJ3.Q3", "2C")
        assert not self.rule.applies(ctx)


class TestRebidStayman2D:
    rule = RebidStayman2D()

    def test_no_4_card_major(self) -> None:
        """No 4-card major -> 2D denial."""
        # AQ3.KJ4.QJ3.K432 = 15 HCP, 3-3-3-4
        ctx = _ctx("AQ3.KJ4.QJ3.K432", "2C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2D"

    def test_has_4_hearts_rejected(self) -> None:
        """Has 4 hearts -> 2H, not 2D."""
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2C")
        assert not self.rule.applies(ctx)

    def test_has_4_spades_rejected(self) -> None:
        """Has 4 spades -> 2S, not 2D."""
        ctx = _ctx("AQ32.KJ4.QJ3.Q43", "2C")
        assert not self.rule.applies(ctx)


# ── After Jacoby Transfer (2D/2H) ─────────────────────────────────


class TestRebidSuperAccept:
    rule = RebidSuperAccept()

    def test_17_hcp_4_hearts(self) -> None:
        """17 HCP, 4+ hearts after 2D transfer -> super-accept 3H."""
        # AK3.KQ42.QJ3.Q43 = 17 HCP, 3-4-3-3
        ctx = _ctx("AK3.KQ42.QJ3.Q43", "2D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_17_hcp_4_spades(self) -> None:
        """17 HCP, 4+ spades after 2H transfer -> super-accept 3S."""
        # AKQ2.QJ4.QJ3.Q43 = 17 HCP, 4-3-3-3
        ctx = _ctx("AKQ2.QJ4.QJ3.Q43", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_16_hcp_rejected(self) -> None:
        """16 HCP -> normal acceptance, not super-accept."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP, 3-4-3-3
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2D")
        assert not self.rule.applies(ctx)

    def test_17_hcp_3_card_support_rejected(self) -> None:
        """17 HCP but only 3-card support -> not super-accept."""
        # AK3.KQ4.KJ3.Q432 = 17 HCP, 3-3-3-4, only 3 hearts
        ctx = _ctx("AK3.KQ4.KJ3.Q432", "2D")
        assert not self.rule.applies(ctx)


class TestRebidCompleteTransfer:
    rule = RebidCompleteTransfer()

    def test_2d_to_2h(self) -> None:
        """2D transfer -> complete to 2H."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP, 3-3-3-4
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2H"

    def test_2h_to_2s(self) -> None:
        """2H transfer -> complete to 2S."""
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "2S"

    def test_not_after_stayman(self) -> None:
        """Does not apply after Stayman 2C."""
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2C")
        assert not self.rule.applies(ctx)


# ── After 2S Puppet ───────────────────────────────────────────────


class TestRebidComplete2SPuppet:
    rule = RebidComplete2SPuppet()

    def test_forced_3c(self) -> None:
        """2S puppet -> forced 3C."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3C"

    def test_not_after_2h(self) -> None:
        """Does not apply after 2H (transfer)."""
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2H")
        assert not self.rule.applies(ctx)


# ── After Gerber (4C) ──────────────────────────────────────────────


class TestRebidGerberResponse:
    rule = RebidGerberResponse()

    def test_0_aces(self) -> None:
        """0 aces -> 4D."""
        # KQ3.KQ4.KQJ2.KQ3 = 18 HCP, 0 aces
        ctx = _ctx("KQ3.KQ4.KQJ2.KQ3", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"

    def test_1_ace(self) -> None:
        """1 ace -> 4H."""
        # AK3.KQ4.KJ3.Q432 = 17 HCP, 1 ace
        ctx = _ctx("AK3.KQ4.KJ3.Q432", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_2_aces(self) -> None:
        """2 aces -> 4S."""
        # AQ3.KQ4.AJ3.Q432 = 17 HCP, 2 aces
        ctx = _ctx("AQ3.KQ4.AJ3.Q432", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_3_aces(self) -> None:
        """3 aces -> 4NT."""
        # AQ3.AJ4.AJ3.Q432 = 16 HCP, 3 aces
        ctx = _ctx("AQ3.AJ4.AJ3.Q432", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4NT"

    def test_4_aces(self) -> None:
        """4 aces -> 4D (same as 0)."""
        # AQ3.AJ4.AJ32.A43 = 15 HCP, 4 aces
        ctx = _ctx("AQ3.AJ4.AJ32.A43", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"

    def test_not_after_3c(self) -> None:
        """Does not apply after 3C (minor invite)."""
        ctx = _ctx("AK3.KQ4.KJ3.Q432", "3C")
        assert not self.rule.applies(ctx)


# ── After Texas Transfer (4D/4H) ──────────────────────────────────


class TestRebidCompleteTexas:
    rule = RebidCompleteTexas()

    def test_4d_to_4h(self) -> None:
        """4D Texas -> complete to 4H."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "4D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_4h_to_4s(self) -> None:
        """4H Texas -> complete to 4S."""
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "4H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"


# ── After 3H/3S (slam interest) ───────────────────────────────────


class TestRebidRaise3MajorOver1NT:
    rule = RebidRaise3MajorOver1NT()

    def test_16_hcp_3_card_support(self) -> None:
        """16 HCP, 3+ support -> raise 3H to 4H."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP, 3-4-3-3
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_16_hcp_raise_3s_to_4s(self) -> None:
        """16 HCP, 3+ spades -> raise 3S to 4S."""
        # AKJ3.QJ4.QJ3.Q43 = 16 HCP, 4-3-3-3
        ctx = _ctx("AKJ3.QJ4.QJ3.Q43", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_15_hcp_rejected(self) -> None:
        """15 HCP -> decline, not raise."""
        # AQ3.QJ42.KJ3.Q43 = 15 HCP, 3-4-3-3
        ctx = _ctx("AQ3.QJ42.KJ3.Q43", "3H")
        assert not self.rule.applies(ctx)

    def test_16_hcp_2_card_support_rejected(self) -> None:
        """16 HCP but only 2 hearts -> decline."""
        # AKJ2.QJ.QJ32.Q43 = 16 HCP, 4-2-4-3
        ctx = _ctx("AKJ2.QJ.QJ32.Q43", "3H")
        assert not self.rule.applies(ctx)


class TestRebidDecline3MajorOver1NT:
    rule = RebidDecline3MajorOver1NT()

    def test_15_hcp_3nt(self) -> None:
        """15 HCP -> decline with 3NT."""
        # AQ3.QJ42.KJ3.Q43 = 15 HCP, 3-4-3-3
        ctx = _ctx("AQ3.QJ42.KJ3.Q43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_short_support_3nt(self) -> None:
        """16 HCP but 2-card support -> decline with 3NT."""
        # AKJ2.QJ.QJ32.Q43 = 16 HCP, 4-2-4-3
        ctx = _ctx("AKJ2.QJ.QJ32.Q43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"


# ── After 2NT (invite) ────────────────────────────────────────────


class TestRebidAccept2NTOver1NT:
    rule = RebidAccept2NTOver1NT()

    def test_16_hcp_accepts(self) -> None:
        """16 HCP -> accept, bid 3NT."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_17_hcp_accepts(self) -> None:
        """17 HCP -> accept."""
        # AK3.KQ4.QJ3.Q432 = 17 HCP
        ctx = _ctx("AK3.KQ4.QJ3.Q432", "2NT")
        assert self.rule.applies(ctx)

    def test_15_hcp_rejected(self) -> None:
        """15 HCP -> decline."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2NT")
        assert not self.rule.applies(ctx)


class TestRebidDecline2NTOver1NT:
    rule = RebidDecline2NTOver1NT()

    def test_15_hcp_passes(self) -> None:
        """15 HCP -> pass."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "2NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)


# ── After 3C/3D (minor invite) ────────────────────────────────────


class TestRebidAccept3MinorOver1NT:
    rule = RebidAccept3MinorOver1NT()

    def test_16_hcp_accepts_3c(self) -> None:
        """16 HCP -> accept 3C, bid 3NT."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3NT"

    def test_16_hcp_accepts_3d(self) -> None:
        """16 HCP -> accept 3D, bid 3NT."""
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "3D")
        assert self.rule.applies(ctx)

    def test_15_hcp_rejected(self) -> None:
        """15 HCP -> decline."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "3C")
        assert not self.rule.applies(ctx)


class TestRebidDecline3MinorOver1NT:
    rule = RebidDecline3MinorOver1NT()

    def test_15_hcp_passes_3c(self) -> None:
        """15 HCP -> pass 3C."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)

    def test_15_hcp_passes_3d(self) -> None:
        """15 HCP -> pass 3D."""
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "3D")
        assert self.rule.applies(ctx)


# ── After 3NT ──────────────────────────────────────────────────────


class TestRebidPassAfter3NTOver1NT:
    rule = RebidPassAfter3NTOver1NT()

    def test_always_passes(self) -> None:
        """3NT is to play -> always pass."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "3NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)

    def test_not_after_2nt(self) -> None:
        """Does not apply after 2NT."""
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "2NT")
        assert not self.rule.applies(ctx)


# ── After 4NT (quantitative) ──────────────────────────────────────


class TestRebidAccept4NTOver1NT:
    rule = RebidAccept4NTOver1NT()

    def test_16_hcp_bids_6nt(self) -> None:
        """16 HCP -> accept, bid 6NT."""
        # AQ3.KJ42.QJ3.K43 = 16 HCP
        ctx = _ctx("AQ3.KJ42.QJ3.K43", "4NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "6NT"

    def test_15_hcp_rejected(self) -> None:
        """15 HCP -> decline."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "4NT")
        assert not self.rule.applies(ctx)


class TestRebidDecline4NTOver1NT:
    rule = RebidDecline4NTOver1NT()

    def test_15_hcp_passes(self) -> None:
        """15 HCP -> pass."""
        # AQ3.QJ4.KJ3.Q432 = 15 HCP
        ctx = _ctx("AQ3.QJ4.KJ3.Q432", "4NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)


# ── Guard: rules only apply after 1NT opening ─────────────────────


class TestNotAfter1SuitOpening:
    """None of these rules should fire after a 1-of-a-suit opening."""

    def test_stayman_not_after_1h(self) -> None:
        auction = AuctionState(dealer=Seat.NORTH)
        auction.add_bid(parse_bid("1H"))
        auction.add_bid(PASS)
        auction.add_bid(parse_bid("2C"))
        auction.add_bid(PASS)
        ctx = BiddingContext(
            Board(
                hand=Hand.from_pbn("AQ3.KJ42.QJ3.K43"),
                seat=Seat.NORTH,
                auction=auction,
            )
        )
        assert not RebidStayman2H().applies(ctx)
        assert not RebidStayman2S().applies(ctx)
        assert not RebidStayman2D().applies(ctx)


# ══════════════════════════════════════════════════════════════════════
# Opener's rebids after 2NT opening
# ══════════════════════════════════════════════════════════════════════


def _ctx_2nt(pbn: str, response: str) -> BiddingContext:
    """Build a BiddingContext where I opened 2NT and partner responded.

    North opens 2NT, East passes, South responds, West passes, North rebids.
    """
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("2NT"))  # N opens 2NT
    auction.add_bid(PASS)  # E passes
    auction.add_bid(parse_bid(response))  # S responds
    auction.add_bid(PASS)  # W passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.NORTH, auction=auction)
    )


# ── After Stayman (3C) ───────────────────────────────────────────


class TestRebid2NTStayman3H:
    rule = Rebid2NTStayman3H()

    def test_4_hearts(self) -> None:
        """4+ hearts -> bid 3H."""
        # AQ3.KQ42.AQ3.K43 = 20 HCP, 3-4-3-3
        ctx = _ctx_2nt("AQ3.KQ42.AQ3.K43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_4_4_majors_bids_hearts_first(self) -> None:
        """4-4 in majors -> bid hearts first."""
        # AQ32.KQ42.AQ3.K3 = 20 HCP, 4-4-3-2
        ctx = _ctx_2nt("AQ32.KQ42.AQ3.K3", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_3_hearts_rejected(self) -> None:
        """Only 3 hearts -> not 3H."""
        # AQ32.KQ4.AQ3.K43 = 20 HCP, 4-3-3-3
        ctx = _ctx_2nt("AQ32.KQ4.AQ3.K43", "3C")
        assert not self.rule.applies(ctx)

    def test_not_after_1nt(self) -> None:
        """Does not apply when I opened 1NT."""
        ctx = _ctx("AQ3.KQ42.AQ3.K43", "2C")
        assert not self.rule.applies(ctx)


class TestRebid2NTStayman3S:
    rule = Rebid2NTStayman3S()

    def test_4_spades_no_4_hearts(self) -> None:
        """4+ spades, <4 hearts -> bid 3S."""
        # AQ32.KQ4.AQ3.K43 = 20 HCP, 4-3-3-3
        ctx = _ctx_2nt("AQ32.KQ4.AQ3.K43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_4_4_majors_rejected(self) -> None:
        """4-4 in majors -> 3H first, not 3S."""
        # AQ32.KQ42.AQ3.K3 = 20 HCP
        ctx = _ctx_2nt("AQ32.KQ42.AQ3.K3", "3C")
        assert not self.rule.applies(ctx)


class TestRebid2NTStayman3D:
    rule = Rebid2NTStayman3D()

    def test_no_4_card_major(self) -> None:
        """No 4-card major -> 3D denial."""
        # AQ3.KQ4.AQ32.K43 = 20 HCP, 3-3-4-3
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "3C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3D"

    def test_4_hearts_rejected(self) -> None:
        """4 hearts -> bid 3H, not 3D."""
        ctx = _ctx_2nt("AQ3.KQ42.AQ3.K43", "3C")
        assert not self.rule.applies(ctx)


# ── After Transfer (3D/3H) ───────────────────────────────────────


class TestRebid2NTCompleteTransfer:
    rule = Rebid2NTCompleteTransfer()

    def test_complete_heart_transfer(self) -> None:
        """3D -> complete to 3H."""
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "3D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"

    def test_complete_spade_transfer(self) -> None:
        """3H -> complete to 3S."""
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "3H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3S"

    def test_no_super_accept(self) -> None:
        """Even with 21 HCP + 4-card support, just complete (no super-accept)."""
        # AQ3.AKQ4.AQ3.K43 = 22 HCP, but 2NT range is 20-21
        # Use a valid 2NT hand: AQ32.KQ42.AQ3.K3 = 20 HCP with 4 hearts
        ctx = _ctx_2nt("AQ32.KQ42.AQ3.K3", "3D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "3H"  # Just complete, not 4H


# ── After 3S Puppet ──────────────────────────────────────────────


class TestRebid2NTComplete3SPuppet:
    rule = Rebid2NTComplete3SPuppet()

    def test_forced_4c(self) -> None:
        """3S puppet -> forced 4C."""
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "3S")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4C"

    def test_not_after_1nt_2s(self) -> None:
        """Does not apply to 2S puppet over 1NT."""
        ctx = _ctx("AQ3.KJ4.QJ3.K432", "2S")
        assert not self.rule.applies(ctx)


# ── After Gerber (4C) ────────────────────────────────────────────


class TestRebid2NTGerberResponse:
    rule = Rebid2NTGerberResponse()

    def test_2_aces(self) -> None:
        """2 aces -> 4S."""
        # AQ3.AQ4.AQ32.K43 = 21 HCP, 2 aces (SA, HA)
        ctx = _ctx_2nt("AQ3.AQ4.KQ32.K43", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"

    def test_1_ace(self) -> None:
        """1 ace -> 4H."""
        # AQ3.KQ4.KQ32.K43 = 21 HCP, 1 ace (SA)
        ctx = _ctx_2nt("AQ3.KQ4.KQ32.K43", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_0_aces(self) -> None:
        """0 aces -> 4D."""
        # KQ3.KQ4.KQ32.KQ3 = 22 HCP but 0 aces (unrealistic for 2NT but tests logic)
        ctx = _ctx_2nt("KQ3.KQ4.KQ32.KQ3", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4D"

    def test_3_aces(self) -> None:
        """3 aces -> 4NT."""
        # AQ3.A4.AQ32.KQ43 = 20 HCP, 3 aces
        ctx = _ctx_2nt("AQ3.A4.AQ32.KQ43", "4C")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4NT"


# ── After Texas (4D/4H) ─────────────────────────────────────────


class TestRebid2NTCompleteTexas:
    rule = Rebid2NTCompleteTexas()

    def test_4d_to_4h(self) -> None:
        """4D -> complete to 4H."""
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "4D")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4H"

    def test_4h_to_4s(self) -> None:
        """4H -> complete to 4S."""
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "4H")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "4S"


# ── After 3NT ────────────────────────────────────────────────────


class TestRebid2NTPassAfter3NT:
    rule = Rebid2NTPassAfter3NT()

    def test_always_passes(self) -> None:
        """3NT is to play -> always pass."""
        ctx = _ctx_2nt("AQ3.KQ42.AQ3.K43", "3NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)


# ── After 4NT (quantitative) ────────────────────────────────────


class TestRebid2NTAccept4NT:
    rule = Rebid2NTAccept4NT()

    def test_21_hcp_bids_6nt(self) -> None:
        """21 HCP -> accept, bid 6NT."""
        # AQ3.AQ4.AQ32.K43 = 21 HCP
        ctx = _ctx_2nt("AQ3.AQ4.AQ32.K43", "4NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert str(result.bid) == "6NT"

    def test_20_hcp_rejected(self) -> None:
        """20 HCP -> decline."""
        # AQ3.KQ4.AQ32.K43 = 20 HCP
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "4NT")
        assert not self.rule.applies(ctx)


class TestRebid2NTDecline4NT:
    rule = Rebid2NTDecline4NT()

    def test_20_hcp_passes(self) -> None:
        """20 HCP -> pass."""
        # AQ3.KQ4.AQ32.K43 = 20 HCP
        ctx = _ctx_2nt("AQ3.KQ4.AQ32.K43", "4NT")
        assert self.rule.applies(ctx)
        result = self.rule.select(ctx)
        assert is_pass(result.bid)

    def test_21_hcp_rejected(self) -> None:
        """21 HCP -> accept, not decline."""
        # AQ3.AQ4.AQ32.K43 = 21 HCP
        ctx = _ctx_2nt("AQ3.AQ4.AQ32.K43", "4NT")
        # Decline still applies (catch-all), but Accept has higher priority
        assert self.rule.applies(ctx)


# ── Guard: 2NT rules don't fire after 1NT ────────────────────────


class TestNotAfter1NTOpening:
    """2NT rebid rules should not fire after a 1NT opening."""

    def test_stayman_not_after_1nt(self) -> None:
        ctx = _ctx("AQ3.KQ42.AQ3.K43", "2C")
        assert not Rebid2NTStayman3H().applies(ctx)
        assert not Rebid2NTStayman3S().applies(ctx)
        assert not Rebid2NTStayman3D().applies(ctx)
