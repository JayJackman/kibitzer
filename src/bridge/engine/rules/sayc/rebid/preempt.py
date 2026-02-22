"""Opener's rebid rules after preemptive openings -- SAYC.

Rebid rules for when I opened a preemptive bid and partner has responded.
- Weak two (2D/2H/2S): after 2NT feature ask, after new suit, catch-all pass
- 3-level preempt (3C/3D/3H/3S): after new suit, catch-all pass
- 4-level preempt (4C/4D/4H/4S): always pass

All rules belong to Category.REBID_OPENER.
"""

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import Rank, Suit

# -- Helpers -----------------------------------------------------------------


def _my_opened_suit(ctx: BiddingContext) -> Suit:
    """The suit I opened."""
    assert ctx.my_bids
    bid = ctx.my_bids[0]
    assert is_suit_bid(bid)
    return bid.suit


def _opened_weak_two_self(ctx: BiddingContext) -> bool:
    """Whether I opened a weak two (2D/2H/2S)."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return (
        is_suit_bid(bid)
        and bid.level == 2
        and bid.suit
        in (
            Suit.DIAMONDS,
            Suit.HEARTS,
            Suit.SPADES,
        )
    )


def _opened_3_level_self(ctx: BiddingContext) -> bool:
    """Whether I opened a 3-level preempt."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 3 and bid.suit != Suit.NOTRUMP


def _opened_4_level_self(ctx: BiddingContext) -> bool:
    """Whether I opened a 4-level preempt."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 4 and bid.suit != Suit.NOTRUMP


def _partner_bid_2nt(ctx: BiddingContext) -> bool:
    """Whether partner responded 2NT (feature ask after weak two)."""
    resp = ctx.partner_last_bid
    return (
        resp is not None
        and is_suit_bid(resp)
        and resp.level == 2
        and resp.suit == Suit.NOTRUMP
    )


def _partner_bid_new_suit(ctx: BiddingContext) -> bool:
    """Whether partner responded in a new suit (not my suit, not NT)."""
    resp = ctx.partner_last_bid
    if resp is None or not is_suit_bid(resp):
        return False
    if resp.suit == Suit.NOTRUMP:
        return False
    return resp.suit != _my_opened_suit(ctx)


def _partner_suit(ctx: BiddingContext) -> Suit:
    """Partner's response suit."""
    resp = ctx.partner_last_bid
    assert resp is not None and is_suit_bid(resp)
    return resp.suit


def _find_feature(ctx: BiddingContext) -> Suit | None:
    """Find cheapest outside suit with a feature (ace or protected king Kx+).

    Returns the suit to bid at the 3-level, or None if no feature.
    Iterates in standard bidding order (C < D < H < S) for cheapest.
    """
    my_suit = _my_opened_suit(ctx)
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == my_suit:
            continue
        if ctx.hand.has_card(suit, Rank.ACE):
            return suit
        if ctx.hand.has_card(suit, Rank.KING) and ctx.hand.suit_length(suit) >= 2:
            return suit
    return None


# ===========================================================================
# B4: Weak Two Rebids
# ===========================================================================

# -- After 2NT feature ask --------------------------------------------------


class RebidShowFeature(Rule):
    """Show a feature after 2NT ask -- maximum with outside ace or protected king.

    e.g. 2H->2NT->3C (ace of clubs), 2S->2NT->3D (king of diamonds)

    SAYC: "Maximum with feature: show feature (outside ace or protected king)."
    """

    @property
    def name(self) -> str:
        return "rebid.show_feature"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 588

    def applies(self, ctx: BiddingContext) -> bool:
        return (
            _opened_weak_two_self(ctx)
            and _partner_bid_2nt(ctx)
            and ctx.hcp >= 9
            and _find_feature(ctx) is not None
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _find_feature(ctx)
        assert suit is not None
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"Maximum, feature in {suit.name.lower()} -- "
                "showing outside ace or protected king"
            ),
            forcing=True,
        )


class Rebid3NTAfterFeatureAsk(Rule):
    """Bid 3NT after 2NT ask -- maximum, no outside feature.

    e.g. 2H->2NT->3NT

    SAYC: "Maximum, no feature: bid 3NT."
    """

    @property
    def name(self) -> str:
        return "rebid.3nt_after_feature_ask"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 586

    def applies(self, ctx: BiddingContext) -> bool:
        return (
            _opened_weak_two_self(ctx)
            and _partner_bid_2nt(ctx)
            and ctx.hcp >= 9
            and _find_feature(ctx) is None
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Maximum, no feature -- 3NT after 2NT ask",
            forcing=False,
        )


class RebidOwnSuitAfterFeatureAsk(Rule):
    """Rebid own suit after 2NT ask -- minimum, sign off.

    e.g. 2H->2NT->3H, 2S->2NT->3S

    SAYC: "Minimum (5-8 HCP): rebid own suit at 3-level."
    """

    @property
    def name(self) -> str:
        return "rebid.own_suit_after_feature_ask"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 584

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_weak_two_self(ctx) and _partner_bid_2nt(ctx) and ctx.hcp <= 8

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opened_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(f"Minimum -- rebid {suit.name.lower()} after 2NT ask"),
            forcing=False,
        )


# -- After new suit response ------------------------------------------------


class RebidRaiseNewSuitWeakTwo(Rule):
    """Raise partner's new suit after weak two -- 3+ support.

    e.g. 2H->2S->3S, 2S->3C->4C

    SAYC: "3+ card support for responder's suit: raise."
    """

    @property
    def name(self) -> str:
        return "rebid.raise_new_suit_weak_two"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 582

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_weak_two_self(ctx) or not _partner_bid_new_suit(ctx):
            return False
        return ctx.hand.suit_length(_partner_suit(ctx)) >= 3

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp = ctx.partner_last_bid
        assert resp is not None and is_suit_bid(resp)
        return RuleResult(
            bid=SuitBid(resp.level + 1, resp.suit),
            rule_name=self.name,
            explanation=(
                f"3+ {resp.suit.name.lower()} support -- raise after weak two"
            ),
            forcing=False,
        )


class RebidOwnSuitAfterNewSuitWeakTwo(Rule):
    """Rebid own suit after new suit response to weak two -- no fit.

    e.g. 2H->2S->3H, 2S->3C->3S

    SAYC: "No fit: rebid own suit at cheapest level."
    """

    @property
    def name(self) -> str:
        return "rebid.own_suit_after_new_suit_weak_two"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 579

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_weak_two_self(ctx) and _partner_bid_new_suit(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opened_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"No fit -- rebid {suit.name.lower()} after new suit",
            forcing=False,
        )


# -- Catch-all pass ----------------------------------------------------------


class RebidPassAfterWeakTwo(Rule):
    """Pass after weak two -- catch-all for non-forcing responses.

    e.g. 2H->3H->Pass, 2S->4S->Pass, 2H->3NT->Pass

    After raise, 3NT, or game raise, opener passes.
    Also lowest-priority catch-all for any weak two rebid situation.
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_weak_two"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 577

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_weak_two_self(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass after weak two",
            forcing=False,
        )


# ===========================================================================
# B5: 3-Level Preempt Rebids
# ===========================================================================


class RebidRaiseAfterNewSuit3Level(Rule):
    """Raise partner's new suit after 3-level preempt -- 3+ support.

    e.g. 3C->3H->4H, 3D->3S->4S

    SAYC: "3+ card support for responder's suit: raise."
    """

    @property
    def name(self) -> str:
        return "rebid.raise_after_new_suit_3_level"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 576

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_3_level_self(ctx) or not _partner_bid_new_suit(ctx):
            return False
        return ctx.hand.suit_length(_partner_suit(ctx)) >= 3

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp = ctx.partner_last_bid
        assert resp is not None and is_suit_bid(resp)
        return RuleResult(
            bid=SuitBid(resp.level + 1, resp.suit),
            rule_name=self.name,
            explanation=(
                f"3+ {resp.suit.name.lower()} support -- raise after 3-level preempt"
            ),
            forcing=False,
        )


class RebidOwnSuitAfterNewSuit3Level(Rule):
    """Rebid own suit after new suit response to 3-level preempt -- no fit.

    e.g. 3C->3H->4C, 3D->3S->4D

    Rebid at the 4-level (cheapest available).
    """

    @property
    def name(self) -> str:
        return "rebid.own_suit_after_new_suit_3_level"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 573

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_3_level_self(ctx) and _partner_bid_new_suit(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opened_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"No fit -- rebid {suit.name.lower()} after new suit",
            forcing=False,
        )


class RebidPassAfter3Level(Rule):
    """Pass after 3-level preempt -- catch-all.

    e.g. 3H->4H->Pass, 3C->3NT->Pass

    After raise, 3NT, or game raise, opener passes.
    Also lowest-priority catch-all for any 3-level rebid situation.
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_3_level"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 571

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_3_level_self(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass after 3-level preempt",
            forcing=False,
        )


# ===========================================================================
# B6: 4-Level Preempt Rebids
# ===========================================================================


class RebidPassAfter4Level(Rule):
    """Pass after 4-level preempt -- always.

    e.g. 4H->Pass->Pass, 4C->5C->Pass
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_4_level"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 568

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_4_level_self(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass after 4-level preempt",
            forcing=False,
        )
