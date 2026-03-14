"""Responder's rebid after Stayman over 1NT or 2NT -- SAYC.

Covers all reresponse decisions after responder bid Stayman (2C over 1NT,
3C over 2NT) and opener showed or denied a 4-card major.

Reference: research/05-conventions.md lines 30-46.
"""

from __future__ import annotations

from bridge.engine.condition import (
    All,
    Condition,
    HasMajor,
    HasMinor,
    HasSuitFit,
    HcpRange,
    Not,
    SuitLength,
)
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    i_bid_stayman_1nt,
    i_bid_stayman_2nt,
    partner_denied_major,
    partner_opened_1nt,
    partner_opened_2nt,
    partner_showed_a_major,
    shown_major,
)

__all__ = [
    # Section A: After 1NT - 2C - 2D (Stayman denial over 1NT)
    "PassGarbageStayman",
    "InviteMajorAfterDenial",
    "Invite2NTAfterDenial",
    "GFMajorAfterDenial",
    "Game3NTAfterDenial",
    "SlamMinorAfterDenial",
    # Section B: After 1NT - 2C - 2H/2S (Stayman fit over 1NT)
    "PassGarbageStaymanFit",
    "InviteRaiseStaymanFit",
    "GameRaiseStaymanFit",
    "Invite2NTStaymanNoFit",
    "Game3NTStaymanNoFit",
    # Section C: After 2NT - 3C - 3D (Stayman denial over 2NT)
    "GFMajor2NTDenial",
    "Game3NT2NTDenial",
    "SlamMinor2NTDenial",
    "Quant4NT2NTDenial",
    # Section D: After 2NT - 3C - 3H/3S (Stayman fit over 2NT)
    "GameRaise2NTStaymanFit",
    "Game3NT2NTNoFit",
    "Quant4NT2NTStaymanFit",
]


# ── helpers ─────────────────────────────────────────────────────


def _longest_major(ctx: BiddingContext) -> Suit:
    """Return the longer major; spades with equal length."""
    if ctx.hand.num_hearts > ctx.hand.num_spades:
        return Suit.HEARTS
    return Suit.SPADES


def _longest_minor(ctx: BiddingContext) -> Suit:
    """Return the longer minor; clubs with equal length."""
    if ctx.hand.num_diamonds > ctx.hand.num_clubs:
        return Suit.DIAMONDS
    return Suit.CLUBS


_has_5_card_major = HasMajor(min_len=5)
_has_5_card_minor = HasMinor(min_len=5)
_fit_in_shown_major = HasSuitFit(shown_major, min_len=4)


# ── Section A: After 1NT - 2C - 2D (Stayman denial over 1NT) ──


class PassGarbageStayman(Rule):
    """Pass 2D with garbage Stayman hand.

    1NT - 2C - 2D - Pass.  Weak hand with 4-4 in the majors.
    Garbage Stayman planned to pass any response -- 2D is as good a
    spot as any.  SAYC: may use Stayman with fewer HCP when holding
    both 4-card majors.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_garbage_stayman"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 55

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(max_hcp=7),
            SuitLength(Suit.HEARTS, min_len=4),
            SuitLength(Suit.SPADES, min_len=4),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation=("Garbage Stayman -- no major found, weak hand, pass 2D"),
        )


class InviteMajorAfterDenial(Rule):
    """Show a 5-card major at the 2-level as invitational.

    1NT - 2C - 2D - 2H/2S.  8-9 HCP with a 5-card major.
    Invitational -- opener can pass, raise, or bid 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_major_after_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 240

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), _has_5_card_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.HEARTS), SuitBid(2, Suit.SPADES)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=(
                f"8-9 HCP, 5-card {suit.name.lower()} -- invitational 2{suit.letter}"
            ),
        )


class Invite2NTAfterDenial(Rule):
    """Invite with 2NT after Stayman denial.

    1NT - 2C - 2D - 2NT.  8-9 HCP, no 5-card major.
    Natural invitational -- opener passes or bids 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_2nt_after_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 235

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), Not(_has_5_card_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8-9 HCP, no major fit found -- invitational 2NT",
        )


class GFMajorAfterDenial(Rule):
    """Show a 5-card major at the 3-level as game-forcing.

    1NT - 2C - 2D - 3H/3S.  10-15 HCP with a 5-card major.
    Game forcing -- opener can raise with 3-card support or bid 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.gf_major_after_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 340

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), _has_5_card_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.HEARTS), SuitBid(3, Suit.SPADES)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"10-15 HCP, 5-card {suit.name.lower()} -- game-forcing 3{suit.letter}"
            ),
        )


class Game3NTAfterDenial(Rule):
    """Bid 3NT after Stayman denial with game values.

    1NT - 2C - 2D - 3NT.  10-15 HCP, no 5-card major.
    Sign-off in game.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_after_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 335

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), Not(_has_5_card_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-15 HCP, no major fit -- game in 3NT",
        )


class SlamMinorAfterDenial(Rule):
    """Show a long minor with slam interest after Stayman denial.

    1NT - 2C - 2D - 3C/3D.  16+ HCP, 5+ cards in a minor.
    Forcing -- exploring slam potential.
    """

    @property
    def name(self) -> str:
        return "reresponse.slam_minor_after_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 450

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=16), _has_5_card_minor)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.CLUBS), SuitBid(3, Suit.DIAMONDS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_minor(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"16+ HCP, 5+ {suit.name.lower()} -- slam interest, 3{suit.letter}"
            ),
            forcing=True,
        )


# ── Section B: After 1NT - 2C - 2H/2S (Stayman fit over 1NT) ──


class PassGarbageStaymanFit(Rule):
    """Pass with garbage Stayman hand after finding a major fit.

    1NT - 2C - 2H/2S - Pass.  Weak hand (0-7 HCP), 4+ cards in
    partner's shown major.  Garbage Stayman found a playable spot.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_garbage_stayman_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 56

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=7), _fit_in_shown_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation=(
                f"Garbage Stayman -- found {major.name.lower()} fit, weak hand, pass"
            ),
        )


class InviteRaiseStaymanFit(Rule):
    """Invite by raising partner's shown major to the 3-level.

    1NT - 2C - 2H - 3H (or 2S - 3S).  8-9 HCP, 4+ card fit.
    Invitational raise -- opener passes or bids game.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_raise_stayman_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 245

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), _fit_in_shown_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        major = shown_major(ctx)
        return frozenset({SuitBid(3, major)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(3, major),
            rule_name=self.name,
            explanation=(
                f"8-9 HCP, 4+ {major.name.lower()} -- "
                f"invitational raise to 3{major.letter}"
            ),
        )


class GameRaiseStaymanFit(Rule):
    """Raise partner's shown major to game.

    1NT - 2C - 2H - 4H (or 2S - 4S).  10-15 HCP, 4+ card fit.
    Game bid -- to play.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_raise_stayman_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 345

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), _fit_in_shown_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        major = shown_major(ctx)
        return frozenset({SuitBid(4, major)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(4, major),
            rule_name=self.name,
            explanation=(
                f"10-15 HCP, 4+ {major.name.lower()} -- game in 4{major.letter}"
            ),
        )


class Invite2NTStaymanNoFit(Rule):
    """Invite with 2NT after partner showed a major we don't fit.

    1NT - 2C - 2H - 2NT (or 2S - 2NT).  8-9 HCP, fewer than 4
    cards in partner's shown major.  Natural invitational.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_2nt_stayman_no_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 230

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), Not(_fit_in_shown_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(f"8-9 HCP, no {major.name.lower()} fit -- invitational 2NT"),
        )


class Game3NTStaymanNoFit(Rule):
    """Bid 3NT after partner showed a major we don't fit.

    1NT - 2C - 2H - 3NT (or 2S - 3NT).  10-15 HCP, fewer than 4
    cards in partner's shown major.  Sign-off in game.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_stayman_no_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 330

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_stayman_1nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), Not(_fit_in_shown_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(f"10-15 HCP, no {major.name.lower()} fit -- game in 3NT"),
        )


# ── Section C: After 2NT - 3C - 3D (Stayman denial over 2NT) ──


class GFMajor2NTDenial(Rule):
    """Show a 5-card major after Stayman denial over 2NT.

    2NT - 3C - 3D - 3H/3S.  5-card major, any HCP (game-forcing
    by default since 2NT shows 20-21 and responder needed 4+ to
    bid Stayman).  Opener raises with 3-card support or bids 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.gf_major_2nt_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 342

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return _has_5_card_major

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.HEARTS), SuitBid(3, Suit.SPADES)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"5-card {suit.name.lower()} over 2NT -- game-forcing 3{suit.letter}"
            ),
            forcing=True,
        )


class Game3NT2NTDenial(Rule):
    """Bid 3NT after Stayman denial over 2NT.

    2NT - 3C - 3D - 3NT.  No 5-card major, not enough for slam.
    Game sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_2nt_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 336

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=11), Not(_has_5_card_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No major fit over 2NT -- game in 3NT",
        )


class SlamMinor2NTDenial(Rule):
    """Show a long minor with slam interest after Stayman denial over 2NT.

    2NT - 3C - 3D - 4C/4D.  12+ HCP, 5+ cards in a minor.
    Forcing -- exploring slam.  Combined points: 32+ minimum.
    """

    @property
    def name(self) -> str:
        return "reresponse.slam_minor_2nt_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 452

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12), _has_5_card_minor)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.CLUBS), SuitBid(4, Suit.DIAMONDS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_minor(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"12+ HCP, 5+ {suit.name.lower()} over 2NT -- "
                f"slam interest, 4{suit.letter}"
            ),
            forcing=True,
        )


class Quant4NT2NTDenial(Rule):
    """Quantitative 4NT after Stayman denial over 2NT.

    2NT - 3C - 3D - 4NT.  12-13 HCP, no 5-card major or minor.
    Invites 6NT -- opener passes with minimum (20) or bids 6NT
    with maximum (21).
    """

    @property
    def name(self) -> str:
        return "reresponse.quant_4nt_2nt_denial"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 448

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_denied_major)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=12, max_hcp=13)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12-13 HCP over 2NT -- quantitative 4NT, inviting 6NT",
        )


# ── Section D: After 2NT - 3C - 3H/3S (Stayman fit over 2NT) ──


class GameRaise2NTStaymanFit(Rule):
    """Raise partner's shown major to game over 2NT.

    2NT - 3C - 3H - 4H (or 3S - 4S).  4+ card fit.
    No invitational level -- 2NT + Stayman values already guarantee
    game.  Sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_raise_2nt_stayman_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 347

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=11), _fit_in_shown_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        major = shown_major(ctx)
        return frozenset({SuitBid(4, major)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(4, major),
            rule_name=self.name,
            explanation=(
                f"4+ {major.name.lower()} fit over 2NT -- game in 4{major.letter}"
            ),
        )


class Game3NT2NTNoFit(Rule):
    """Bid 3NT after partner showed a major we don't fit over 2NT.

    2NT - 3C - 3H - 3NT (or 3S - 3NT).  Fewer than 4 cards in
    partner's major.  Game sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_2nt_no_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 332

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=11), Not(_fit_in_shown_major))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        major = shown_major(ctx)
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(f"No {major.name.lower()} fit over 2NT -- game in 3NT"),
        )


class Quant4NT2NTStaymanFit(Rule):
    """Quantitative 4NT after finding a major fit over 2NT.

    2NT - 3C - 3H - 4NT (or 3S - 4NT).  12-13 HCP, 4+ card fit.
    Invites slam -- opener passes 4NT with minimum or bids 6 of
    the major (or 6NT) with maximum.
    """

    @property
    def name(self) -> str:
        return "reresponse.quant_4nt_2nt_stayman_fit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 446

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_stayman_2nt, partner_showed_a_major)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12, max_hcp=13), _fit_in_shown_major)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "12-13 HCP, major fit over 2NT -- quantitative 4NT, inviting slam"
            ),
        )
