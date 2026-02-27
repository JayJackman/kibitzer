"""Section I: After I Jump Shifted (1x->jump->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import All, Computed, Condition, HcpRange, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import SuitBid
from bridge.model.card import Suit

from .helpers import (
    find_new_suit_forcing,
    my_response,
    my_response_suit,
    opening_bid,
    opening_suit,
    partner_opened_1_suit,
    partner_rebid,
)

__all__ = [
    "Blackwood4NTAfterJS",
    "FourMAfterJS",
    "ShowSecondSuitAfterJS",
    "ThreeNTAfterJSReresponse",
]


# ── Section I helpers ─────────────────────────────────


@condition("I jump-shifted")
def _i_jump_shifted(ctx: BiddingContext) -> bool:
    """I made a jump shift (e.g. 1H->2S)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    if resp.is_notrump or resp.suit == opening.suit:
        return False
    cheapest = cheapest_bid_in_suit(resp.suit, opening)
    return resp.level > cheapest.level


def _find_new_suit_forcing_5plus(ctx: BiddingContext) -> Suit | None:
    """Find a 5+ card new suit for a forcing bid (e.g., second suit after JS)."""
    return find_new_suit_forcing(ctx, min_len=5)


def _agreed_suit_after_js(ctx: BiddingContext) -> Suit | None:
    """Find the agreed suit after a jump shift sequence."""
    opening = opening_suit(ctx)
    my_suit = my_response_suit(ctx)
    rebid = partner_rebid(ctx)
    # If partner raised my suit, that's the agreed suit
    if rebid.suit == my_suit:
        return my_suit
    # If partner rebid their own suit and I have support
    if rebid.suit == opening and ctx.hand.suit_length(opening) >= 3:
        return opening
    # If I have support for partner's rebid suit
    if not rebid.is_notrump and ctx.hand.suit_length(rebid.suit) >= 4:
        return rebid.suit
    return None


@condition("fit established after jump shift")
def _fit_established_after_js(ctx: BiddingContext) -> bool:
    return _agreed_suit_after_js(ctx) is not None


# ── Rules ─────────────────────────────────────────────


class Blackwood4NTAfterJS(Rule):
    """Slam investigation via Blackwood after jump shift.

    19+ pts, fit established.
    """

    @property
    def name(self) -> str:
        return "reresponse.blackwood_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 499

    @property
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_jump_shifted,
            _fit_established_after_js,
            HcpRange(min_hcp=19),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="19+ HCP, fit established -- Blackwood 4NT",
            forcing=True,
        )


class FourMAfterJS(Rule):
    """Bid game in major after jump shift.

    Fit, game values only.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 372

    @property
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_jump_shifted,
            _fit_established_after_js,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        # Find the agreed major
        suit = _agreed_suit_after_js(ctx)
        if suit is not None and suit.is_major:
            return RuleResult(
                bid=SuitBid(4, suit),
                rule_name=self.name,
                explanation=f"Fit established -- game in 4{suit.letter}",
            )
        # Fallback to 3NT
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Fit in minor -- 3NT",
        )


class ShowSecondSuitAfterJS(Rule):
    """Show a second suit after jump shift.

    5-5+ shape, exploring. GF.
    """

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_forcing_5plus, "5+ card new suit")

    @property
    def name(self) -> str:
        return "reresponse.show_second_suit_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 443

    @property
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_jump_shifted,
            self._new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"Show second suit after jump shift -- {bid}",
            forcing=True,
        )


class ThreeNTAfterJSReresponse(Rule):
    """Bid 3NT after jump shift -- no fit, balanced.

    Catch-all for jump shift reresponse.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_js_reresponse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 362

    @property
    def conditions(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_jump_shifted,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No fit after jump shift -- 3NT",
        )
