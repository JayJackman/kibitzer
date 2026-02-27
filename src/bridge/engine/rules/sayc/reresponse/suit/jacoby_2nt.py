"""Section E: After Jacoby 2NT (1M->2NT->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import suit_hcp
from bridge.engine.condition import All, Any, Not, SupportPtsRange, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

from .helpers import (
    opening_bid,
    opening_suit,
    partner_opened_1_suit,
    partner_rebid,
    partner_rebid_3nt,
    partner_rebid_suit,
)

__all__ = [
    "Bid4MAfter3NTMedium",
    "Bid4MAfterMax",
    "Bid4MAfterShortness",
    "Bid4MAfterSource",
    "Blackwood4NTAfter3NTMedium",
    "Blackwood4NTAfterJacoby4M",
    "Blackwood4NTAfterMax",
    "Blackwood4NTAfterShortness",
    "Blackwood4NTAfterSource",
    "PassAfterJacoby4M",
]


# ── Section E helpers ─────────────────────────────────


@condition("I bid Jacoby 2NT")
def _i_bid_jacoby_2nt(ctx: BiddingContext) -> bool:
    """I bid Jacoby 2NT (1M->2NT, major only)."""
    opening = opening_bid(ctx)
    resp = ctx.my_bids[0]
    assert isinstance(resp, SuitBid)
    return resp.is_notrump and resp.level == 2 and opening.suit.is_major


@condition("partner showed shortness (Jacoby)")
def _partner_showed_shortness(ctx: BiddingContext) -> bool:
    """Partner rebid a new suit at the 3-level (singleton/void)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return rebid.level == 3 and rebid.suit != opening.suit and not rebid.is_notrump


@condition("no wasted values in partner's short suit")
def _no_wasted_values_in_short_suit(ctx: BiddingContext) -> bool:
    short_suit = partner_rebid_suit(ctx)
    return suit_hcp(ctx, short_suit) < 4


@condition("partner showed source of tricks (Jacoby)")
def _partner_showed_source(ctx: BiddingContext) -> bool:
    """Partner rebid a new suit at the 4-level (5+ card side suit)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return rebid.level == 4 and rebid.suit != opening.suit and not rebid.is_notrump


@condition("partner rebid 3 of our major (Jacoby max)")
def _partner_rebid_3_major(ctx: BiddingContext) -> bool:
    """Partner rebid 3M (18+ HCP, no shortness)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return rebid.suit == opening.suit and rebid.level == 3


@condition("partner rebid 4 of our major (Jacoby min)")
def _partner_rebid_4_major(ctx: BiddingContext) -> bool:
    """Partner rebid 4M (12-14 HCP, no shortness)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return rebid.suit == opening.suit and rebid.level == 4


# ── Rules ─────────────────────────────────────────────


class Blackwood4NTAfterShortness(Rule):
    """Slam try after opener showed shortness.

    1M->2NT->3x->4NT. 16+ support pts, no wasted values in short suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_shortness"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 498

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_showed_shortness,
            SupportPtsRange(opening_suit, min_pts=16),
            _no_wasted_values_in_short_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16+ support pts, no wasted values -- Blackwood 4NT",
            forcing=True,
        )


class Bid4MAfterShortness(Rule):
    """Settle for game after opener showed shortness.

    1M->2NT->3x->4M. Settle with 13-15 support pts, or 16+ with wasted
    values in partner's short suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_shortness"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 348

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_showed_shortness,
            Any(
                # 13-15 support pts -- always settle for game
                SupportPtsRange(opening_suit, min_pts=13, max_pts=15),
                # 16+ but wasted values in short suit -- also settle
                All(
                    SupportPtsRange(opening_suit, min_pts=16),
                    Not(_no_wasted_values_in_short_suit),
                ),
            ),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Settle for game after shortness -- 4{suit.letter}",
        )


class Blackwood4NTAfterSource(Rule):
    """Slam try after opener showed source of tricks.

    1M->2NT->4x->4NT. 16+ support pts with fitting honors.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_source"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 449

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_showed_source,
            SupportPtsRange(opening_suit, min_pts=16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16+ support pts after source of tricks -- Blackwood 4NT",
            forcing=True,
        )


class Bid4MAfterSource(Rule):
    """Settle for game after opener showed source of tricks.

    1M->2NT->4x->4M. 13-15 support pts.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_source"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 346

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_showed_source,
            SupportPtsRange(opening_suit, min_pts=13, max_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13-15 support pts after source of tricks -- 4{suit.letter}",
        )


class Blackwood4NTAfterMax(Rule):
    """Slam try after opener showed maximum.

    1M->2NT->3M->4NT. 15+ support pts.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_max"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 448

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_rebid_3_major,
            SupportPtsRange(opening_suit, min_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15+ support pts after 3M maximum -- Blackwood 4NT",
            forcing=True,
        )


class Bid4MAfterMax(Rule):
    """Settle for game after opener showed maximum.

    1M->2NT->3M->4M. 13-14 support pts.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_max"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 345

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_rebid_3_major,
            SupportPtsRange(opening_suit, min_pts=13, max_pts=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13-14 support pts after 3M maximum -- 4{suit.letter}",
        )


class Blackwood4NTAfter3NTMedium(Rule):
    """Slam try after opener showed medium hand.

    1M->2NT->3NT->4NT. 18+ support pts.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_3nt_medium"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 447

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            partner_rebid_3nt,
            SupportPtsRange(opening_suit, min_pts=18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="18+ support pts after 3NT medium -- Blackwood 4NT",
            forcing=True,
        )


class Bid4MAfter3NTMedium(Rule):
    """Correct to 4M after opener showed medium hand.

    1M->2NT->3NT->4M. Trump suit agreed, play in major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_3nt_medium"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 344

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            partner_rebid_3nt,
            SupportPtsRange(opening_suit, min_pts=13, max_pts=17),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13-17 spts after 3NT medium -- correct to 4{suit.letter}",
        )


class Blackwood4NTAfterJacoby4M(Rule):
    """Slam try after opener showed minimum.

    1M->2NT->4M->4NT. 18+ support pts, slam try with maximum.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_jacoby_4m"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 446

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_rebid_4_major,
            SupportPtsRange(opening_suit, min_pts=18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="18+ support pts after 4M minimum -- Blackwood 4NT",
            forcing=True,
        )


class PassAfterJacoby4M(Rule):
    """Pass after opener showed minimum.

    1M->2NT->4M->Pass. Game reached, no slam.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_jacoby_4m"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 85

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_jacoby_2nt,
            _partner_rebid_4_major,
            SupportPtsRange(opening_suit, max_pts=17),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="13-17 support pts after 4M minimum -- pass",
        )
