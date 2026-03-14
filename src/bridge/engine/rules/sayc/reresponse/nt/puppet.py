"""Responder's rebid after puppet to 3C/4C over 1NT or 2NT -- SAYC.

Covers the simple minor-suit signoff sequences:
- 1NT - 2S - 3C - Pass (clubs) or 3D (diamonds)
- 2NT - 3S - 4C - Pass (clubs) or 4D (diamonds)

Reference: research/05-conventions.md lines 202-219.
"""

from __future__ import annotations

from bridge.engine.condition import All, Condition, HcpRange, SuitLength
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    i_bid_puppet_1nt,
    i_bid_puppet_2nt,
    partner_completed_puppet,
    partner_opened_1nt,
    partner_opened_2nt,
)

__all__ = [
    # Section H: After puppet completion over 1NT
    "PassPuppetClubs",
    "CorrectPuppetDiamonds",
    # Section I: After puppet completion over 2NT
    "PassPuppet2NTClubs",
    "CorrectPuppet2NTDiamonds",
]


# ── Section H: After puppet completion over 1NT ──────────────


class PassPuppetClubs(Rule):
    """Pass after puppet to 3C with a weak hand and long clubs.

    1NT - 2S - 3C - Pass.  0-7 HCP, 6+ clubs.  Sign-off in 3C.
    SAYC: 2S over 1NT is puppet to 3C for minor sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_puppet_clubs"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 54

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1nt,
            i_bid_puppet_1nt,
            partner_completed_puppet,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(max_hcp=7),
            SuitLength(Suit.CLUBS, min_len=6),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="0-7 HCP, 6+ clubs -- sign-off in 3C via puppet",
            forcing=False,
        )


class CorrectPuppetDiamonds(Rule):
    """Correct to 3D after puppet to 3C with a weak hand and long diamonds.

    1NT - 2S - 3C - 3D.  0-7 HCP, 6+ diamonds.  Sign-off in 3D.
    SAYC: 2S over 1NT is puppet to 3C; bid 3D with diamonds.
    """

    @property
    def name(self) -> str:
        return "reresponse.correct_puppet_diamonds"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 53

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1nt,
            i_bid_puppet_1nt,
            partner_completed_puppet,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(max_hcp=7),
            SuitLength(Suit.DIAMONDS, min_len=6),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.DIAMONDS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.DIAMONDS),
            rule_name=self.name,
            explanation="0-7 HCP, 6+ diamonds -- correct puppet to 3D sign-off",
            forcing=False,
        )


# ── Section I: After puppet completion over 2NT ──────────────


class PassPuppet2NTClubs(Rule):
    """Pass after puppet to 4C with a weak hand and long clubs.

    2NT - 3S - 4C - Pass.  0-3 HCP, 6+ clubs.  Sign-off in 4C.
    SAYC: 3S over 2NT is puppet to 4C for minor sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_puppet_2nt_clubs"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 55

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_2nt,
            i_bid_puppet_2nt,
            partner_completed_puppet,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(max_hcp=3),
            SuitLength(Suit.CLUBS, min_len=6),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="0-3 HCP, 6+ clubs -- sign-off in 4C via puppet",
            forcing=False,
        )


class CorrectPuppet2NTDiamonds(Rule):
    """Correct to 4D after puppet to 4C with a weak hand and long diamonds.

    2NT - 3S - 4C - 4D.  0-3 HCP, 6+ diamonds.  Sign-off in 4D.
    SAYC: 3S over 2NT is puppet to 4C; bid 4D with diamonds.
    """

    @property
    def name(self) -> str:
        return "reresponse.correct_puppet_2nt_diamonds"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 54

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_2nt,
            i_bid_puppet_2nt,
            partner_completed_puppet,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(max_hcp=3),
            SuitLength(Suit.DIAMONDS, min_len=6),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.DIAMONDS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.DIAMONDS),
            rule_name=self.name,
            explanation="0-3 HCP, 6+ diamonds -- correct puppet to 4D sign-off",
            forcing=False,
        )
