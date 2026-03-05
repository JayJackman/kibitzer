"""Preemptive opening bid rules — SAYC weak twos and 3/4-level preempts."""

from bridge.engine.condition import All, Condition, HcpRange, NoVoid, SuitFinderComputed
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.evaluate import has_outside_four_card_major, quality_suit
from bridge.model.bid import SuitBid
from bridge.model.card import SUITS_SHDC, Suit


def _find_weak_two_suit(ctx: BiddingContext) -> Suit | None:
    """Find the suit for a weak two, or None if requirements aren't met."""
    hand = ctx.hand
    for suit in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS):
        if (
            hand.suit_length(suit) == 6
            and quality_suit(hand, suit)
            and not has_outside_four_card_major(hand, suit)
        ):
            return suit
    return None


def _find_preempt3_suit(ctx: BiddingContext) -> Suit | None:
    """Find a 7-card suit suitable for a 3-level preempt."""
    hand = ctx.hand
    for suit in SUITS_SHDC:
        if (
            hand.suit_length(suit) == 7
            and quality_suit(hand, suit)
            and not has_outside_four_card_major(hand, suit)
        ):
            return suit
    return None


def _find_preempt4_suit(ctx: BiddingContext) -> Suit | None:
    """Find a suit suitable for a 4-level preempt."""
    hand = ctx.hand
    for suit in SUITS_SHDC:
        length = hand.suit_length(suit)
        min_length = 7 if suit.is_major else 8
        if length >= min_length and quality_suit(hand, suit):
            return suit
    return None


class OpenWeakTwo(Rule):
    """Open a weak two (2D, 2H, 2S) with 5-11 HCP and a 6-card suit.

    SAYC: "5-11 HCP, 6-card suit of reasonable quality. No void.
    No outside 4-card major."

    2C is reserved for the strong artificial opening.
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_weak_two_suit,
            "6-card suit for weak two",
            min_len=6,
        )

    @property
    def name(self) -> str:
        return "opening.weak_two"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 200

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(5, 11), NoVoid(), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=f"5-11 HCP, 6-card {suit.letter} — SAYC weak two",
        )


class OpenPreempt3(Rule):
    """Open at the 3-level with a 7-card suit and less than opening strength.

    SAYC: "7-card suit, too weak to open at the 1-level."
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_preempt3_suit,
            "7-card suit for preempt",
            min_len=7,
        )

    @property
    def name(self) -> str:
        return "opening.preempt_3"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 170

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=11), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"7-card {suit.letter}, preemptive — SAYC 3-level preempt",
        )


class OpenPreempt4(Rule):
    """Open at the 4-level with an 8+ card suit (or 7+ card major).

    SAYC: "8+ card suit (4H/4S may be opened with 7+), less than
    opening strength."
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_preempt4_suit,
            "long suit for 4-level preempt",
            min_len=7,
        )

    @property
    def name(self) -> str:
        return "opening.preempt_4"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 180

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=11), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        min_length = "7" if suit.is_major else "8"
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"{min_length}+ card {suit.letter}, preemptive — SAYC 4-level preempt"
            ),
        )
