"""Strong 2C opening bid rule — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import SuitBid
from bridge.model.card import Suit


class Open2C(Rule):
    """Open 2C with 22+ total points.

    SAYC: "Strong, artificial 2C opening: 22+ HCP, or the playing
    equivalent with a very strong unbalanced hand."

    Uses total_pts (HCP + length points) >= 22 to approximate
    "playing equivalent."
    """

    @property
    def name(self) -> str:
        return "opening.2c"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 450

    def applies(self, ctx: BiddingContext) -> bool:
        return ctx.total_pts >= 22

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.CLUBS),
            rule_name=self.name,
            explanation="22+ total points — SAYC strong artificial 2C",
            alerts=("Artificial, strong, forcing",),
            forcing=True,
        )
