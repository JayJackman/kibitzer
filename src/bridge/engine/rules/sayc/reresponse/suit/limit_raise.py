"""After I Limit Raised (1x->3x->rebid->?)."""

from __future__ import annotations

from bridge.engine.condition import All, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Rank, Suit

from .helpers import (
    my_response,
    opening_bid,
    partner_opened_1_suit,
    partner_rebid,
)

__all__ = [
    "BlackwoodResponseAfterLimitRaise",
    "PassAfterAcceptedLimitRaise",
]


# ── helpers ─────────────────────────────────


@condition("I limit-raised opener's suit")
def _i_limit_raised(ctx: BiddingContext) -> bool:
    """I limit-raised (e.g. 1H->3H)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 2


@condition("partner bid 4NT (Blackwood)")
def _partner_bid_4nt(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return rebid.is_notrump and rebid.level == 4


@condition("partner accepted limit raise")
def _partner_accepted_limit_raise(ctx: BiddingContext) -> bool:
    """Partner bid game after my limit raise (3M->4M, 3m->3NT/5m)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    if opening.suit.is_major:
        return rebid.suit == opening.suit and rebid.level == 4
    return (rebid.is_notrump and rebid.level == 3) or (
        rebid.suit == opening.suit and rebid.level == 5
    )


# ── Rules ─────────────────────────────────────────────


class PassAfterAcceptedLimitRaise(Rule):
    """Pass after opener accepted limit raise.

    1M->3M->4M->Pass. Game reached.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_accepted_limit_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 88

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_limit_raised,
            _partner_accepted_limit_raise,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after limit raise -- pass",
        )


class BlackwoodResponseAfterLimitRaise(Rule):
    """Respond to Blackwood 4NT after limit raise.

    1x->3x->4NT->5C/5D/5H/5S. Show ace count.
    SAYC: 5C=0/4 aces, 5D=1, 5H=2, 5S=3.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_response_after_limit_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 500

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_limit_raised,
            _partner_bid_4nt,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        aces = sum(
            ctx.hand.has_card(s, Rank.ACE)
            for s in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES)
        )
        response_map = {
            0: (Suit.CLUBS, "0/4"),
            1: (Suit.DIAMONDS, "1"),
            2: (Suit.HEARTS, "2"),
            3: (Suit.SPADES, "3"),
            4: (Suit.CLUBS, "0/4"),
        }
        suit, desc = response_map[aces]
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"{desc} aces -- Blackwood response",
            forcing=True,
            alerts=(f"Blackwood response -- showing {desc} aces",),
        )
