"""After I Jump Shifted (1x->jump->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import All, Computed, Condition, HcpRange, Not, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

from .helpers import (
    find_new_suit_forcing,
    my_response,
    my_response_suit,
    my_response_suit_6plus,
    opening_bid,
    opening_suit,
    partner_opened_1_suit,
    partner_rebid,
)

__all__ = [
    "Blackwood4NTAfterJS",
    "FourMAfterJS",
    "PassAtGameAfterJS",
    "PreferenceToOpeningSuitAfterJS",
    "RebidOwnSuitAfterJSReresponse",
    "ShowSecondSuitAfterJS",
    "ThreeNTAfterJSReresponse",
]


# ── helpers ─────────────────────────────────


@condition("I jump-shifted")
def _i_jump_shifted(ctx: BiddingContext) -> bool:
    """I made a jump shift (e.g. 1H->2S)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    if resp.is_notrump or resp.suit == opening.suit:
        return False
    cheapest = cheapest_bid_in_suit(resp.suit, opening)
    if cheapest is None:
        return False
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


@condition("auction is at game level after jump shift")
def _auction_at_game(ctx: BiddingContext) -> bool:
    """Partner's rebid is at game level (3NT, 4M, or higher)."""
    rebid = partner_rebid(ctx)
    if rebid.is_notrump and rebid.level >= 3:
        return True
    return rebid.level >= 4


@condition("partner rebid a new suit after JS")
def _partner_rebid_new_suit_after_js(ctx: BiddingContext) -> bool:
    """Partner bid a suit that is neither their opening suit nor my JS suit."""
    rebid = partner_rebid(ctx)
    if rebid.is_notrump:
        return False
    return rebid.suit != opening_suit(ctx) and rebid.suit != my_response_suit(ctx)


@condition("3+ cards in opener's suit")
def _support_for_opening_suit(ctx: BiddingContext) -> bool:
    return ctx.hand.suit_length(opening_suit(ctx)) >= 3


# ── After fit established ────────────────────────────────────────


class Blackwood4NTAfterJS(Rule):
    """Slam investigation via Blackwood after jump shift.

    21+ HCP, fit established. With 21+ responder + 12+ opener = 33+,
    true slam territory.
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
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return All(_fit_established_after_js, HcpRange(min_hcp=21))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="21+ HCP, fit established -- Blackwood 4NT",
            forcing=True,
        )


class FourMAfterJS(Rule):
    """Bid game in major (or 3NT for minor) after jump shift.

    Fit established, auction below game level.
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
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted, Not(_auction_at_game))

    @property
    def conditions(self) -> Condition:
        return _fit_established_after_js

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _agreed_suit_after_js(ctx)
        if suit is not None and suit.is_major:
            return RuleResult(
                bid=SuitBid(4, suit),
                rule_name=self.name,
                explanation=f"Fit established -- game in 4{suit.letter}",
            )
        # Minor fit -- 3NT
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Fit in minor -- 3NT",
        )


# ── Exploring (no fit yet) ───────────────────────────────────────


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
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return self._new_suit

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"Show second suit after jump shift -- {bid}",
            forcing=True,
        )


class RebidOwnSuitAfterJSReresponse(Rule):
    """Rebid own 6+ card suit after jump shift.

    No fit found, 6+ cards in JS suit. Still forcing, exploring.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 430

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return All(my_response_suit_6plus, Not(_fit_established_after_js))

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6+ card suit, rebid after jump shift -- {bid}",
            forcing=True,
        )


class PreferenceToOpeningSuitAfterJS(Rule):
    """Give preference to opener's first suit after jump shift.

    Partner bid a new suit, no fit established, 3+ in opener's suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 400

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_jump_shifted,
            _partner_rebid_new_suit_after_js,
        )

    @property
    def conditions(self) -> Condition:
        return All(_support_for_opening_suit, Not(_fit_established_after_js))

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"Preference to opener's suit after jump shift -- {bid}",
            forcing=True,
        )


# ── Catch-all / game reached ─────────────────────────────────────


class ThreeNTAfterJSReresponse(Rule):
    """Bid 3NT after jump shift -- no fit, balanced.

    Catch-all for jump shift reresponse when auction is below game.
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
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted, Not(_auction_at_game))

    @property
    def conditions(self) -> Condition:
        return All()

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No fit after jump shift -- 3NT",
        )


class PassAtGameAfterJS(Rule):
    """Pass when auction is at game level after jump shift.

    Game reached (partner bid 3NT or 4+), no slam interest.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_at_game_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 88

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_jump_shifted, _auction_at_game)

    @property
    def conditions(self) -> Condition:
        return All()

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after jump shift -- pass",
        )
