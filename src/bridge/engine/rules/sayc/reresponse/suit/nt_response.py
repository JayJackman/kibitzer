"""After I Bid 3NT Over Major/Minor."""

from __future__ import annotations

from bridge.engine.condition import All, Condition, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid

from .helpers import (
    my_response,
    partner_opened_1_suit,
)

__all__ = [
    "PassAfter3NTResponse",
]


# ── helpers ─────────────────────────────────


@condition("I bid 3NT")
def _i_bid_3nt(ctx: BiddingContext) -> bool:
    resp = my_response(ctx)
    return resp.is_notrump and resp.level == 3


# ── Rules ─────────────────────────────────────────────


class PassAfter3NTResponse(Rule):
    """Pass after I bid 3NT.

    Let opener decide. Default pass.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_3nt_response"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 89

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_3nt)

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="After 3NT response -- pass",
        )
