"""Sign-off passes for responder's rebid after a 1NT or 2NT opening -- SAYC.

Covers terminal pass bids for NT auction paths:
- PassAfterTexas: game reached after Texas transfer completion
- PassAfterNTReresponse: catch-all pass for any NT auction

Reference: research/02-responses.md (Texas transfers), planning/reresponses.md
sections E and G.
"""

from __future__ import annotations

from bridge.engine.condition import All, Any, Condition
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid

from .helpers import (
    i_bid_texas_1nt,
    i_bid_texas_2nt,
    partner_completed_texas,
    partner_opened_1nt,
    partner_opened_2nt,
)

__all__ = [
    "PassAfterTexas",
    "PassAfterNTReresponse",
]


# ── Pass after Texas transfer ────────────────────────────────


class PassAfterTexas(Rule):
    """Pass after Texas transfer completion -- game reached.

    1NT->4D->4H->Pass or 1NT->4H->4S->Pass (same for 2NT).
    Texas was a game-level sign-off; opener completed the transfer.
    SAYC: responder always passes after Texas completion.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_texas"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 55

    @property
    def prerequisites(self) -> Condition:
        return All(
            Any(
                All(partner_opened_1nt, i_bid_texas_1nt),
                All(partner_opened_2nt, i_bid_texas_2nt),
            ),
            partner_completed_texas,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached via Texas transfer -- pass",
            forcing=False,
        )


# ── Catch-all pass after NT opening ─────────────────────────


class PassAfterNTReresponse(Rule):
    """Catch-all pass for any NT auction not covered by a specific rule.

    Lowest-priority pass for responder's second bid after a 1NT or 2NT
    opening. More specific rules (Stayman, transfer, Gerber, Texas,
    puppet) fire first; this handles anything that falls through.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 50

    @property
    def prerequisites(self) -> Condition:
        return Any(partner_opened_1nt, partner_opened_2nt)

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="No further action after NT opening -- pass",
            forcing=False,
        )
