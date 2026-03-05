"""Responses to preemptive openings (weak twos, 3-level, 4-level) -- SAYC.

Response rules for when partner opens a preemptive bid:
- Weak two (2D/2H/2S): game raise, 3NT, new suit, 2NT feature ask, raise, pass
- 3-level preempt (3C/3D/3H/3S): game raise, 3NT, new suit, raise, pass
- 4-level preempt (4C/4D/4H/4S): raise (minors only), pass
"""

from __future__ import annotations

from bridge.engine.condition import (
    All,
    Any,
    Condition,
    HasSuitFit,
    HcpRange,
    SuitFinderComputed,
    SupportPtsRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.evaluate import has_stopper
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Suit

# -- Helpers -----------------------------------------------------------------


def _opening_suit(ctx: BiddingContext) -> Suit:
    """The suit partner opened.

    Only safe to call from select() methods or conditions guarded by a
    partner-opened check.
    """
    assert ctx.opening_bid is not None
    _, bid = ctx.opening_bid
    assert is_suit_bid(bid)
    return bid.suit


def _opening_suit_safe(ctx: BiddingContext) -> Suit | None:
    """The suit partner opened, or None if no suit opening exists."""
    if ctx.opening_bid is None:
        return None
    _, bid = ctx.opening_bid
    if not is_suit_bid(bid):
        return None
    return bid.suit


# -- Conditions --------------------------------------------------------------


@condition("partner opened a weak two")
def _partner_opened_weak_2(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return (
        is_suit_bid(bid)
        and bid.level == 2
        and bid.suit in (Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES)
    )


@condition("partner opened at the 3-level")
def _partner_opened_3_level(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 3 and not bid.is_notrump


@condition("partner opened at the 4-level")
def _partner_opened_4_level(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 4 and not bid.is_notrump


@condition("stoppers in all unbid suits")
def _stoppers_in_unbid(ctx: BiddingContext) -> bool:
    if (opened := _opening_suit_safe(ctx)) is None:
        return False
    return all(has_stopper(ctx.hand, s) for s in SUITS_SHDC if s != opened)


@condition("opener's suit is a major")
def _opener_is_major(ctx: BiddingContext) -> bool:
    if (suit := _opening_suit_safe(ctx)) is None:
        return False
    return suit.is_major


@condition("opener's suit is a minor")
def _opener_is_minor(ctx: BiddingContext) -> bool:
    if (suit := _opening_suit_safe(ctx)) is None:
        return False
    return suit.is_minor


def _find_new_suit_over_2(ctx: BiddingContext) -> Suit | None:
    """Find a 5+ card new suit to bid over a weak two.

    Returns the longest qualifying suit (higher rank breaks ties), or None.
    The suit must differ from partner's opened suit.
    """
    if (opened := _opening_suit_safe(ctx)) is None:
        return None
    best: Suit | None = None
    best_len = 0
    for suit in SUITS_SHDC:
        if suit == opened:
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 5 and length > best_len:
            best = suit
            best_len = length
    return best


def _find_new_suit_over_3(ctx: BiddingContext) -> Suit | None:
    """Find a 5+ card suit ranking higher than partner's 3-level preempt.

    Must be higher-ranking to stay at the 3-level. Returns the longest
    qualifying suit (higher rank breaks ties), or None.
    """
    if (opened := _opening_suit_safe(ctx)) is None:
        return None
    best: Suit | None = None
    best_len = 0
    for suit in SUITS_SHDC:
        if suit.value <= opened.value:
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 5 and length > best_len:
            best = suit
            best_len = length
    return best


# ===========================================================================
# B4: Responses to Weak Two (2D/2H/2S)
# ===========================================================================


class RespondGameRaiseWeakTwoMajor(Rule):
    """Game raise over partner's weak two in a major.

    e.g. 2H->4H, 2S->4S

    SAYC: "Jump raise to game -- to play; may be preemptive with
    good support."  3+ support with 14+ support pts (game values),
    or 5+ support (preemptive).
    """

    @property
    def name(self) -> str:
        return "response.game_raise_weak_two_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 488

    @property
    def prerequisites(self) -> Condition:
        return All(_partner_opened_weak_2, _opener_is_major)

    @property
    def conditions(self) -> Condition:
        return Any(
            # Preemptive: 5+ support
            HasSuitFit(_opening_suit, min_len=5),
            # Game values: 14+ support pts
            All(
                HasSuitFit(_opening_suit, min_len=3),
                SupportPtsRange(_opening_suit, min_pts=14),
            ),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Game raise over weak {suit.name.lower()} -- to play",
            forcing=False,
        )


class RespondGameRaiseWeakTwoMinor(Rule):
    """Game raise over partner's weak two in a minor.

    e.g. 2D->5D

    SAYC: "Jump raise to game -- to play."
    3+ support with 16+ support pts (game values).
    """

    @property
    def name(self) -> str:
        return "response.game_raise_weak_two_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 488

    @property
    def prerequisites(self) -> Condition:
        return All(_partner_opened_weak_2, _opener_is_minor)

    @property
    def conditions(self) -> Condition:
        return All(
            HasSuitFit(_opening_suit, min_len=3),
            SupportPtsRange(_opening_suit, min_pts=16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"Game raise over weak {suit.name.lower()} -- to play",
            forcing=False,
        )


class Respond3NTOverWeakTwo(Rule):
    """3NT over partner's weak two -- stoppers and game values.

    e.g. 2H->3NT, 2S->3NT, 2D->3NT

    SAYC: "3NT -- to play."  Requires stoppers in all unbid suits
    and 15+ HCP.
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_weak_two"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 486

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_weak_2

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=15), _stoppers_in_unbid)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15+ HCP, stoppers -- 3NT to play over weak two",
            forcing=False,
        )


class RespondNewSuitOverWeakTwo(Rule):
    """New suit over partner's weak two -- forcing one round.

    e.g. 2H->2S, 2D->2H, 2S->3C

    SAYC: "New suit: 5+ cards; forcing one round (RONF)."
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_new_suit_over_2,
            "5+ card new suit",
            min_len=5,
        )

    @property
    def name(self) -> str:
        return "response.new_suit_weak_two"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 482

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_weak_2

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=14), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        opened = _opening_suit(ctx)
        level = 2 if suit.value > opened.value else 3
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(
                f"5+ {suit.name.lower()} -- new suit over weak two, forcing one round"
            ),
            forcing=True,
        )


class Respond2NTFeatureAsk(Rule):
    """2NT feature ask over partner's weak two.

    e.g. 2H->2NT, 2S->2NT, 2D->2NT

    SAYC: "2NT -- forcing; game interest."  Asks opener to describe
    hand: minimum (rebid suit), maximum with feature (show feature),
    maximum without feature (3NT).
    """

    @property
    def name(self) -> str:
        return "response.2nt_feature_ask"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 478

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_weak_2

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=14)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="14+ HCP, game interest -- 2NT feature ask",
            forcing=True,
        )


class RespondRaiseWeakTwo(Rule):
    """Preemptive raise of partner's weak two.

    e.g. 2H->3H, 2S->3S, 2D->3D

    SAYC: "Raise -- to play; often preemptive; does not show extras."
    """

    @property
    def name(self) -> str:
        return "response.raise_weak_two"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 476

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_weak_2

    @property
    def conditions(self) -> Condition:
        return HasSuitFit(_opening_suit, min_len=3)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"3+ {suit.name.lower()} support -- preemptive raise",
            forcing=False,
        )


class RespondPassOverWeakTwo(Rule):
    """Pass over partner's weak two -- default.

    e.g. 2H->Pass, 2S->Pass, 2D->Pass
    """

    @property
    def name(self) -> str:
        return "response.pass_over_weak_two"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 46

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_weak_2

    @property
    def conditions(self) -> Condition:
        return All()

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass over weak two",
            forcing=False,
        )


# ===========================================================================
# B5: Responses to 3-Level Preempts (3C/3D/3H/3S)
# ===========================================================================


class RespondGameRaise3LevelMajor(Rule):
    """Game raise over partner's 3-level major preempt.

    e.g. 3H->4H, 3S->4S

    SAYC: "Jump raise to game -- to play."
    3+ support with 14+ support pts (game values).
    """

    @property
    def name(self) -> str:
        return "response.game_raise_3_level_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 487

    @property
    def prerequisites(self) -> Condition:
        return All(_partner_opened_3_level, _opener_is_major)

    @property
    def conditions(self) -> Condition:
        return All(
            HasSuitFit(_opening_suit, min_len=3),
            SupportPtsRange(_opening_suit, min_pts=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Game raise over 3{suit.name[0]} -- to play",
            forcing=False,
        )


class RespondGameRaise3LevelMinor(Rule):
    """Game raise over partner's 3-level minor preempt.

    e.g. 3C->5C, 3D->5D

    SAYC: "Jump raise to game -- to play."
    3+ support with 16+ support pts (game values).
    """

    @property
    def name(self) -> str:
        return "response.game_raise_3_level_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 487

    @property
    def prerequisites(self) -> Condition:
        return All(_partner_opened_3_level, _opener_is_minor)

    @property
    def conditions(self) -> Condition:
        return All(
            HasSuitFit(_opening_suit, min_len=3),
            SupportPtsRange(_opening_suit, min_pts=16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"Game raise over 3{suit.name[0]} -- to play",
            forcing=False,
        )


class Respond3NTOver3Level(Rule):
    """3NT over partner's 3-level preempt.

    e.g. 3C->3NT, 3D->3NT, 3H->3NT, 3S->3NT

    SAYC: "3NT -- to play."  Requires stoppers and game values.
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_3_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 483

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_3_level

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=15), _stoppers_in_unbid)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15+ HCP, stoppers -- 3NT to play over 3-level preempt",
            forcing=False,
        )


class RespondNewSuitOver3Level(Rule):
    """New suit over partner's 3-level preempt -- forcing one round.

    e.g. 3C->3D, 3C->3H, 3C->3S, 3D->3H, 3D->3S, 3H->3S

    SAYC: "New suit below game: 5+ cards; forcing one round."
    Must be a higher-ranking suit to stay at the 3-level.
    Over 3S, no new suit at the 3-level is possible.
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_new_suit_over_3,
            "5+ card higher-ranking suit",
            min_len=5,
        )

    @property
    def name(self) -> str:
        return "response.new_suit_3_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 481

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_3_level

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=14), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"5+ {suit.name.lower()} -- new suit over 3-level preempt, "
                "forcing one round"
            ),
            forcing=True,
        )


class RespondRaise3Level(Rule):
    """Preemptive raise of partner's 3-level preempt.

    e.g. 3C->4C, 3D->4D, 3H->4H, 3S->4S

    SAYC: "Raise -- preemptive; to play."
    """

    @property
    def name(self) -> str:
        return "response.raise_3_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 473

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_3_level

    @property
    def conditions(self) -> Condition:
        return HasSuitFit(_opening_suit, min_len=3)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"3+ {suit.name.lower()} support -- preemptive raise",
            forcing=False,
        )


class RespondPassOver3Level(Rule):
    """Pass over partner's 3-level preempt -- default.

    e.g. 3C->Pass, 3D->Pass, 3H->Pass, 3S->Pass
    """

    @property
    def name(self) -> str:
        return "response.pass_over_3_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 43

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_3_level

    @property
    def conditions(self) -> Condition:
        return All()

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass over 3-level preempt",
            forcing=False,
        )


# ===========================================================================
# B6: Responses to 4-Level Preempts (4C/4D/4H/4S)
# ===========================================================================


class RespondRaise4Level(Rule):
    """Raise partner's 4-level minor preempt to game.

    e.g. 4C->5C, 4D->5D

    Only over 4C/4D (raising to 5C/5D). Requires 4+ support and
    game values.
    """

    @property
    def name(self) -> str:
        return "response.raise_4_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 474

    @property
    def prerequisites(self) -> Condition:
        return All(_partner_opened_4_level, _opener_is_minor)

    @property
    def conditions(self) -> Condition:
        return All(
            HasSuitFit(_opening_suit, min_len=4),
            SupportPtsRange(_opening_suit, min_pts=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"4+ support, game values -- raise to 5{suit.name[0]}",
            forcing=False,
        )


class RespondPassOver4Level(Rule):
    """Pass over partner's 4-level preempt -- default.

    e.g. 4C->Pass, 4D->Pass, 4H->Pass, 4S->Pass
    """

    @property
    def name(self) -> str:
        return "response.pass_over_4_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 42

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_4_level

    @property
    def conditions(self) -> Condition:
        return All()

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Pass over 4-level preempt",
            forcing=False,
        )
