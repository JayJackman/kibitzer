"""Responder's rebid after Gerber (4C) over 1NT or 2NT -- SAYC.

Covers the three reresponse decisions after partner answers 4C:
- King-ask (5C) when combined aces >= 3
- Sign-off at 4NT when combined aces <= 2 and partner bid below 4NT
- Pass when combined aces <= 2 and partner bid 4NT

Since the bids and logic are identical for 1NT and 2NT Gerber,
rules combine both using Any() prerequisites.

Reference: research/06-slam.md lines 39-73.
"""

from __future__ import annotations

from bridge.engine.condition import All, Any, Condition
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    enough_aces_for_slam,
    i_bid_gerber_1nt,
    i_bid_gerber_2nt,
    not_enough_aces_for_slam,
    partner_opened_1nt,
    partner_opened_2nt,
    partner_responded_4nt,
    partner_responded_below_4nt,
    partner_responded_to_gerber,
)

__all__ = [
    "KingAskAfterGerber",
    "SignoffAfterGerber",
    "PassAfterGerber",
]

# Shared prerequisites: I used Gerber over either 1NT or 2NT.
_gerber_prereqs = Any(
    All(partner_opened_1nt, i_bid_gerber_1nt),
    All(partner_opened_2nt, i_bid_gerber_2nt),
)


# ── King-ask after Gerber ──────────────────────────────────────


class KingAskAfterGerber(Rule):
    """Ask for kings (5C) after Gerber when combined aces >= 3.

    1NT/2NT - 4C - (4D/4H/4S/4NT) - 5C.
    With enough aces for slam, ask for kings to decide 6NT vs 7NT.
    SAYC: 5C after Gerber is the king-ask convention.
    """

    @property
    def name(self) -> str:
        return "reresponse.king_ask_after_gerber"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 450

    @property
    def prerequisites(self) -> Condition:
        return All(
            _gerber_prereqs,
            partner_responded_to_gerber,
        )

    @property
    def conditions(self) -> Condition:
        return enough_aces_for_slam

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(5, Suit.CLUBS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(5, Suit.CLUBS),
            rule_name=self.name,
            explanation="Combined 3+ aces -- ask for kings via 5C",
            forcing=True,
        )


# ── Sign-off after Gerber ──────────────────────────────────────


class SignoffAfterGerber(Rule):
    """Sign off at 4NT when not enough aces and partner bid below 4NT.

    1NT/2NT - 4C - (4D/4H/4S) - 4NT.
    With combined aces <= 2, sign off at 4NT to play.
    SAYC: 4NT after Gerber response is to play (not Blackwood).
    """

    @property
    def name(self) -> str:
        return "reresponse.signoff_after_gerber"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 340

    @property
    def prerequisites(self) -> Condition:
        return All(
            _gerber_prereqs,
            partner_responded_below_4nt,
        )

    @property
    def conditions(self) -> Condition:
        return not_enough_aces_for_slam

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Not enough aces for slam -- sign off at 4NT",
            forcing=False,
        )


# ── Pass after Gerber ──────────────────────────────────────────


class PassAfterGerber(Rule):
    """Pass when not enough aces and partner bid 4NT (3 aces).

    1NT/2NT - 4C - 4NT - Pass.
    With combined aces <= 2, sign off by passing partner's 4NT.
    SAYC: pass is the sign-off when partner's response is already 4NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_gerber"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 340

    @property
    def prerequisites(self) -> Condition:
        return All(
            _gerber_prereqs,
            partner_responded_4nt,
        )

    @property
    def conditions(self) -> Condition:
        return not_enough_aces_for_slam

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Not enough aces for slam -- pass partner's 4NT",
            forcing=False,
        )
