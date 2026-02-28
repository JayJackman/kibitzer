"""After I Raised Opener's Major (1M->2M->rebid->?)."""

from __future__ import annotations

from bridge.engine.condition import All, Any, SupportPtsRange, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Rank, Suit

from .helpers import (
    i_raised,
    opening_bid,
    opening_suit,
    partner_opened_1_suit,
    partner_rebid,
    partner_rebid_suit,
)

__all__ = [
    "AcceptGameTry",
    "AcceptReraise",
    "DeclineGameTry",
    "DeclineReraise",
    "PassAfterGame",
]


# ── helpers ─────────────────────────────────


@condition("partner re-raised our major")
def _partner_reraised_major(ctx: BiddingContext) -> bool:
    """Partner raised again after I single-raised (1M->2M->3M)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return (
        i_raised(ctx)
        and opening.suit.is_major
        and rebid.suit == opening.suit
        and rebid.level == 3
    )


@condition("partner game-tried")
def _partner_game_tried(ctx: BiddingContext) -> bool:
    """Partner bid a new suit after I raised (help suit game try).

    After 1H->2H the try suit may be at the 2-level (2S) or 3-level (3C/3D).
    After 1S->2S the try suits are always at the 3-level (3C/3D/3H).
    """
    if not i_raised(ctx):
        return False
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return (
        opening.suit.is_major
        and rebid.suit != opening.suit
        and not rebid.is_notrump
        and rebid.level <= 3
    )


@condition("partner bid game in our major")
def _partner_bid_game_major(ctx: BiddingContext) -> bool:
    """Partner bid 4M after I raised (1M->2M->4M)."""
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return opening.suit.is_major and rebid.suit == opening.suit and rebid.level == 4


def _has_help_in_suit(ctx: BiddingContext, suit: Suit) -> bool:
    """Whether I have 'help' in the game-try suit (A/K/Q or shortness)."""
    hand = ctx.hand
    length = hand.suit_length(suit)
    if length <= 1:
        return True  # shortness is help
    return (
        hand.has_card(suit, Rank.ACE)
        or hand.has_card(suit, Rank.KING)
        or hand.has_card(suit, Rank.QUEEN)
    )


@condition("has help in game try suit")
def _has_help_in_try_suit(ctx: BiddingContext) -> bool:
    try_suit = partner_rebid_suit(ctx)
    return _has_help_in_suit(ctx, try_suit)


# ── A1: After Help Suit Game Try (1M->2M->3x new suit->?) ────────


class AcceptGameTry(Rule):
    """Accept game try.

    1M->2M->3x->4M. Accept with near-maximum OR with help in try suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_game_try"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 341

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            i_raised,
            _partner_game_tried,
            Any(
                # Near-maximum -- accept regardless of help
                SupportPtsRange(opening_suit, min_pts=9, max_pts=10),
                # Medium with help in the try suit
                All(
                    SupportPtsRange(opening_suit, min_pts=7, max_pts=8),
                    _has_help_in_try_suit,
                ),
            ),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Accept game try -- 4{suit.letter}",
        )


class DeclineGameTry(Rule):
    """Decline game try -- minimum or no help.

    1M->2M->3x->3M. Return to agreed major at 3-level.
    Catches both dead-minimum hands (6 or fewer) and medium hands
    (7-8) without help in the try suit (those with help are already
    accepted by AcceptGameTry at higher priority).
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_game_try"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 191

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            i_raised,
            _partner_game_tried,
            SupportPtsRange(opening_suit, max_pts=8),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"Decline game try -- 3{suit.letter}",
        )


# ── A2: After Re-raise (1M->2M->3M->?) ──────────────────────────


class AcceptReraise(Rule):
    """Accept opener's re-raise invitation.

    1M->2M->3M->4M. Opener showed ~16-18 pts, invitational.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_reraise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 332

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            i_raised,
            _partner_reraised_major,
            SupportPtsRange(opening_suit, min_pts=8, max_pts=10),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"8-10 support pts, accept invitation -- SAYC 4{suit.letter}",
        )


class DeclineReraise(Rule):
    """Decline opener's re-raise invitation.

    1M->2M->3M->Pass. Minimum of range.
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_reraise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 187

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            i_raised,
            _partner_reraised_major,
            SupportPtsRange(opening_suit, max_pts=7),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-7 support pts, decline invitation -- pass",
        )


# ── A3: After Direct Game (1M->2M->4M->?) ────────────────────────


class PassAfterGame(Rule):
    """Pass after opener bid game directly.

    1M->2M->4M->Pass. Opener placed the contract.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_game"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 86

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            i_raised,
            _partner_bid_game_major,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after raise -- pass",
        )
