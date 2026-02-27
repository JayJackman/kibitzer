"""Section J: After I Bid 2NT Over Minor (1m->2NT->rebid->?)."""

from __future__ import annotations

from bridge.engine.condition import All, Condition, HasSuitFit, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

from .helpers import (
    my_response,
    opening_bid,
    partner_opened_1_suit,
    partner_rebid,
    partner_rebid_3nt,
    partner_rebid_own_suit,
    partner_rebid_suit,
)

__all__ = [
    "PassAfter2NTMinor3NT",
    "Raise3MAfter2NTMinor",
    "ThreeNTAfter2NTMinorMajor",
    "ThreeNTAfter2NTMinorRebid",
]


# ── Section J helpers ─────────────────────────────────


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


# ── Rules ─────────────────────────────────────────────


class Raise3MAfter2NTMinor(Rule):
    """Raise opener's major after 2NT over minor.

    1m->2NT->3M->4M. 4+ fit in M.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_3m_after_2nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 369

    @property
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            _partner_rebid_suit_is_major,
            HasSuitFit(partner_rebid_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"4+ {suit.letter}, game in major -- 4{suit.letter}",
        )


class ThreeNTAfter2NTMinorMajor(Rule):
    """Bid 3NT when no fit for opener's major.

    1m->2NT->3M->3NT. No fit in M.
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
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            _partner_rebid_suit_is_major,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No major fit after 2NT -- 3NT",
        )


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
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            partner_rebid_own_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="After 2NT, opener rebid minor -- 3NT",
        )


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
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2nt_over_minor,
            partner_rebid_3nt,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after 2NT minor -- pass",
        )
