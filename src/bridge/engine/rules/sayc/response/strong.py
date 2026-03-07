"""Responses to 2C (strong, artificial, forcing) opening -- SAYC.

Response rules for when partner opens 2C (22+ total points).
Responses: 2D (waiting, default), 2NT (8+ balanced, positive),
or a natural positive suit bid (8+ HCP, 5+ cards, 2 of top 3 honors).
"""

from bridge.engine.condition import (
    All,
    Balanced,
    Condition,
    HcpRange,
    SuitFinderComputed,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Rank, Suit
from bridge.model.hand import Hand

# -- Helpers -----------------------------------------------------------------


def _has_two_top_three(hand: Hand, suit: Suit) -> bool:
    """Whether a suit has 2+ of {A, K, Q}."""
    return (
        sum(1 for r in (Rank.ACE, Rank.KING, Rank.QUEEN) if hand.has_card(suit, r)) >= 2
    )


def _find_positive_suit(ctx: BiddingContext) -> Suit | None:
    """Longest 5+ card suit with 2 of top 3 honors, or None."""
    best_suit: Suit | None = None
    best_length = 0
    for suit in SUITS_SHDC:
        length = ctx.hand.suit_length(suit)
        if length >= 5 and _has_two_top_three(ctx.hand, suit) and length > best_length:
            best_suit = suit
            best_length = length
    return best_suit


# -- Conditions --------------------------------------------------------------


@condition("partner opened 2C")
def _partner_opened_2c(ctx: BiddingContext) -> bool:
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 2 and bid.suit == Suit.CLUBS


# -- Responses ---------------------------------------------------------------


class Respond2NTOver2C(Rule):
    """2NT -- balanced positive response to 2C.

    SAYC: "2NT shows balanced, 8+ HCP."  Game forcing.
    """

    @property
    def name(self) -> str:
        return "response.2nt_over_2c"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 490

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_2c

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8), Balanced(strict=True))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8+ HCP, balanced -- positive response to 2C",
            forcing=True,
        )


class RespondPositiveSuitOver2C(Rule):
    """Natural positive suit response to 2C.

    SAYC: "Natural positive response: 5+ card suit, 8+ HCP,
    2 of top 3 honors (A, K, Q)."  Game forcing.
    """

    def __init__(self) -> None:
        self._suit = SuitFinderComputed(
            _find_positive_suit,
            "5+ card suit with 2 of top 3",
            min_len=5,
        )

    @property
    def name(self) -> str:
        return "response.positive_suit_2c"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 480

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_2c

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8), self._suit)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset(
            {
                SuitBid(2, Suit.HEARTS),
                SuitBid(2, Suit.SPADES),
                SuitBid(3, Suit.CLUBS),
                SuitBid(3, Suit.DIAMONDS),
            }
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        level = 2 if suit.is_major else 3
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(
                f"8+ HCP, 5+ {suit.name.lower()} with 2 of top 3 honors "
                "-- positive response to 2C"
            ),
            forcing=True,
        )


class Respond2DWaiting(Rule):
    """2D -- artificial waiting response to 2C.

    SAYC: "2D is the conventional waiting response.  May be made
    with any hand, including a good hand waiting to hear opener's suit."
    """

    @property
    def name(self) -> str:
        return "response.2d_waiting"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 470

    @property
    def prerequisites(self) -> Condition:
        return _partner_opened_2c

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.DIAMONDS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.DIAMONDS),
            rule_name=self.name,
            explanation="Artificial waiting response to 2C",
            alerts=("Artificial, waiting",),
            forcing=True,
        )
