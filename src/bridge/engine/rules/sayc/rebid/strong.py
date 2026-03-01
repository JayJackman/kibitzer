"""Opener's rebid rules after 2C (strong, artificial, forcing) opening -- SAYC.

All rebid rules for when I opened 2C and partner has responded.
Covers rebids after 2D (waiting) and after positive responses
(2H/2S/3C/3D suit, or 2NT balanced).

All rules belong to Category.REBID_OPENER.
"""

from bridge.engine.condition import (
    All,
    Any,
    Balanced,
    Condition,
    HasSuitFit,
    HcpRange,
    Not,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Suit

# -- Helpers -----------------------------------------------------------------


@condition("I opened 2C")
def _i_opened_2c(ctx: BiddingContext) -> bool:
    """Whether I opened 2C."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 2 and bid.suit == Suit.CLUBS


def _partner_bid(ctx: BiddingContext) -> SuitBid:
    """Partner's response (always a SuitBid in rebid phase after 2C).

    Only safe to call from select() methods where conditions have already
    verified the precondition. Use _partner_bid_safe() in conditions.
    """
    resp = ctx.partner_last_bid
    assert resp is not None and is_suit_bid(resp)
    return resp


def _partner_bid_safe(ctx: BiddingContext) -> SuitBid | None:
    """Partner's response, or None if partner didn't make a suit bid."""
    resp = ctx.partner_last_bid
    if resp is None or not is_suit_bid(resp):
        return None
    return resp


@condition("partner bid 2D waiting")
def _partner_bid_2d_waiting(ctx: BiddingContext) -> bool:
    """Partner responded 2D (waiting)."""
    if (resp := _partner_bid_safe(ctx)) is None:
        return False
    return resp.level == 2 and resp.suit == Suit.DIAMONDS


@condition("partner gave positive response")
def _partner_positive_response(ctx: BiddingContext) -> bool:
    """Partner made a positive response (anything except 2D waiting)."""
    if _partner_bid_safe(ctx) is None:
        return False
    return not _partner_bid_2d_waiting(ctx)


@condition("partner bid positive suit")
def _partner_positive_suit(ctx: BiddingContext) -> bool:
    """Partner made a positive suit response (2H/2S/3C/3D, not 2NT)."""
    if (resp := _partner_bid_safe(ctx)) is None:
        return False
    if resp.is_notrump:
        return False
    return _partner_positive_response(ctx)


@condition("5+ card suit")
def _has_5_plus_suit(ctx: BiddingContext) -> bool:
    """Whether opener has a 5+ card suit."""
    return any(ctx.hand.suit_length(s) >= 5 for s in SUITS_SHDC)


def _longest_suit(ctx: BiddingContext) -> Suit:
    """Opener's longest suit. Higher rank breaks ties (standard for 5+ suits)."""
    best_suit = Suit.CLUBS
    best_length = 0
    for suit in SUITS_SHDC:
        length = ctx.hand.suit_length(suit)
        if length > best_length:
            best_suit = suit
            best_length = length
    return best_suit


@condition("5+ card unbid suit")
def _has_5_plus_unbid_suit(ctx: BiddingContext) -> bool:
    """Whether opener has a 5+ card suit different from partner's."""
    if (resp := _partner_bid_safe(ctx)) is None:
        return False
    return any(ctx.hand.suit_length(s) >= 5 for s in SUITS_SHDC if s != resp.suit)


def _longest_unbid_suit(ctx: BiddingContext) -> Suit:
    """Opener's longest suit excluding partner's. Higher rank breaks ties."""
    partner_suit = _partner_bid(ctx).suit
    best_suit = Suit.CLUBS
    best_length = 0
    for suit in SUITS_SHDC:
        if suit == partner_suit:
            continue
        length = ctx.hand.suit_length(suit)
        if length > best_length:
            best_suit = suit
            best_length = length
    return best_suit


def _partner_response_suit(ctx: BiddingContext) -> Suit:
    """Partner's response suit (for HasSuitFit)."""
    return _partner_bid(ctx).suit


# -- Rebids after 2D waiting ------------------------------------------------


class Rebid2NTAfter2C(Rule):
    """Rebid 2NT after 2C-2D -- 22-24 HCP, balanced.

    e.g. 2C->2D->2NT

    SAYC: "After 2C-2D, opener rebids 2NT with 22-24 HCP, balanced.
    Stayman and transfers apply."
    """

    @property
    def name(self) -> str:
        return "rebid.2nt_after_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 590

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2c,
            _partner_bid_2d_waiting,
            Balanced(strict=True),
            HcpRange(22, 24),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="22-24 HCP, balanced -- 2NT rebid after 2C-2D",
            forcing=False,
        )


class Rebid3NTAfter2C(Rule):
    """Rebid 3NT after 2C-2D -- 25-27 HCP, balanced.

    e.g. 2C->2D->3NT

    SAYC: "After 2C-2D, opener rebids 3NT with 25-27 HCP, balanced."
    """

    @property
    def name(self) -> str:
        return "rebid.3nt_after_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 585

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2c,
            _partner_bid_2d_waiting,
            Balanced(strict=True),
            HcpRange(min_hcp=25),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="25-27 HCP, balanced -- 3NT rebid after 2C-2D",
            forcing=False,
        )


class RebidSuitAfter2C(Rule):
    """Rebid a natural suit after 2C-2D.

    e.g. 2C->2D->2H, 2C->2D->2S, 2C->2D->3C, 2C->2D->3D

    SAYC: "After 2C-2D, opener bids a suit at the cheapest level
    with 5+ cards. Natural, forcing to 3 of a major or 4 of a minor."
    """

    @property
    def name(self) -> str:
        return "rebid.suit_after_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 580

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2c, _partner_bid_2d_waiting, _has_5_plus_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_suit(ctx)
        level = 2 if suit.is_major else 3
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(f"5+ {suit.name.lower()} -- natural rebid after 2C-2D"),
            forcing=True,
        )


class Rebid2NTAfter2COffshape(Rule):
    """Rebid 2NT after 2C-2D with 4-4-4-1 shape -- no 5+ suit, not balanced.

    e.g. 2C->2D->2NT with AKJx.AKQx.KQJx.x

    Catch-all for the rare case where a 2C opener has 22+ HCP but
    exactly 4-4-4-1 distribution: no 5-card suit to bid naturally
    and not balanced for the standard 2NT rebid. Common expert
    practice is to treat these hands as 2NT despite the singleton,
    since there is no good alternative. Stayman and transfers apply.
    """

    @property
    def name(self) -> str:
        return "rebid.2nt_after_2c_offshape"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 578

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2c,
            _partner_bid_2d_waiting,
            Not(Balanced(strict=True), label="balanced"),
            Not(_has_5_plus_suit),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "22+ HCP, 4-4-4-1 shape -- 2NT despite singleton "
                "(no 5+ suit, common expert practice)"
            ),
            forcing=False,
        )


# -- Rebids after positive response ------------------------------------------


class RebidRaiseAfterPositive2C(Rule):
    """Raise partner's positive suit response with 4+ support.

    e.g. 2C->2H->3H, 2C->2S->3S, 2C->3C->4C, 2C->3D->4D

    Game-forcing auction. A simple raise confirms the fit.
    """

    @property
    def name(self) -> str:
        return "rebid.raise_after_positive_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 598

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2c,
            _partner_positive_suit,
            HasSuitFit(_partner_response_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        partner = _partner_bid(ctx)
        return RuleResult(
            bid=SuitBid(partner.level + 1, partner.suit),
            rule_name=self.name,
            explanation=(
                f"4+ {partner.suit.name.lower()} support "
                "-- raise after positive response to 2C"
            ),
            forcing=True,
        )


class RebidSuitAfterPositive2C(Rule):
    """Bid own 5+ card suit after a positive response to 2C.

    e.g. 2C->2H->2S, 2C->2S->3H, 2C->2NT->3S

    Game-forcing auction. Shows a natural suit.
    """

    @property
    def name(self) -> str:
        return "rebid.suit_after_positive_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 596

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2c,
            _partner_positive_response,
            Any(
                All(_partner_positive_suit, _has_5_plus_unbid_suit),
                All(Not(_partner_positive_suit), _has_5_plus_suit),
            ),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        if _partner_positive_suit(ctx):
            suit = _longest_unbid_suit(ctx)
        else:
            suit = _longest_suit(ctx)
        partner = _partner_bid(ctx)
        level = partner.level if suit.value > partner.suit.value else partner.level + 1
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(
                f"5+ {suit.name.lower()} -- natural bid after positive response to 2C"
            ),
            forcing=True,
        )


class RebidNTAfterPositive2C(Rule):
    """Bid 3NT after a positive response to 2C -- catch-all.

    e.g. 2C->2H->3NT, 2C->2NT->3NT

    Game-forcing auction. With no fit and no 5+ suit to show,
    bid 3NT to reach game.
    """

    @property
    def name(self) -> str:
        return "rebid.nt_after_positive_2c"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 594

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2c, _partner_positive_response)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="3NT -- game reached after positive response to 2C",
            forcing=False,
        )
