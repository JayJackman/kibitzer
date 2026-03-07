"""After I Bid 2NT Over Minor (1m->2NT->rebid->?)."""

from __future__ import annotations

from bridge.engine.condition import All, Condition, HcpRange, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    my_response,
    opening_bid,
    partner_opened_1_suit,
    partner_rebid,
    partner_rebid_3nt,
    partner_rebid_own_suit,
)

__all__ = [
    "AcceptQuantitative4NTMinor",
    "DeclineQuantitative4NTMinor",
    "PassAfter2NTMinor3NT",
    "ThreeNTAfter2NTMinorMajor",
    "ThreeNTAfter2NTMinorRebid",
]


# ── helpers ─────────────────────────────────


@condition("I bid 2NT over minor")
def _i_bid_2nt_over_minor(ctx: BiddingContext) -> bool:
    """I bid 2NT over a minor (1m->2NT, GF)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    return resp.is_notrump and resp.level == 2 and opening.suit.is_minor


@condition("partner rebid suit is major")
def _partner_rebid_suit_is_major(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return not rebid.is_notrump and rebid.suit.is_major


@condition("partner rebid 4NT (quantitative)")
def _partner_rebid_4nt(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return rebid.is_notrump and rebid.level == 4


# ── After opener showed major (1m->2NT->3M) ──────────


class ThreeNTAfter2NTMinorMajor(Rule):
    """Bid 3NT when no fit for opener's major.

    1m->2NT->3M->3NT. 2NT response denies 4-card major,
    so responder has at most 3 cards in M -- 3NT is correct.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2nt_minor_major"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 355

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            _partner_rebid_suit_is_major,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No major fit after 2NT -- 3NT",
        )


# ── After opener rebid minor (1m->2NT->3m) ───────────


class ThreeNTAfter2NTMinorRebid(Rule):
    """Bid 3NT after opener rebid own minor.

    1m->2NT->3m->3NT. Default -- balanced, game values.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2nt_minor_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 354

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            partner_rebid_own_suit,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="After 2NT, opener rebid minor -- 3NT",
        )


# ── After opener bid 3NT (1m->2NT->3NT) ──────────────


class PassAfter2NTMinor3NT(Rule):
    """Pass after opener bid 3NT over 2NT minor.

    1m->2NT->3NT->Pass. Game reached.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_2nt_minor_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 92

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            partner_rebid_3nt,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after 2NT minor -- pass",
        )


# ── After quantitative 4NT (1m->2NT->4NT) ────────────


class AcceptQuantitative4NTMinor(Rule):
    """Accept quantitative 4NT -- bid 6NT with maximum.

    1m->2NT->4NT->6NT. 14-15 HCP (maximum for 2NT response).
    Opener showed 18+ HCP; combined 18+14 = 32+ (slam range).
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_quantitative_4nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 370

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            _partner_rebid_4nt,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=14)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(6, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(6, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="14-15 HCP, accept quantitative 4NT -- 6NT",
        )


class DeclineQuantitative4NTMinor(Rule):
    """Decline quantitative 4NT -- pass with minimum.

    1m->2NT->4NT->Pass. 13 HCP (minimum for 2NT response).
    Opener showed 18+ HCP; combined 18+13 = 31 (not enough for slam).
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_quantitative_4nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 92

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            _partner_rebid_4nt,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=13)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="13 HCP, decline quantitative 4NT -- pass",
        )
