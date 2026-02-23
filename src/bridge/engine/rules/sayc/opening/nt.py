"""NT opening bid rules — SAYC 1NT (15-17) and 2NT (20-21)."""

from bridge.engine.condition import All, Balanced, Condition, HcpRange
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import SuitBid
from bridge.model.card import Suit


class Open1NT(Rule):
    """Open 1NT with 15-17 HCP and balanced shape.

    SAYC: "15-17 HCP, balanced. May contain a 5-card major or minor."
    """

    @property
    def name(self) -> str:
        return "opening.1nt"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 250

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(15, 17), Balanced(strict=True))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15-17 HCP, balanced — SAYC 1NT opening",
        )


class Open2NT(Rule):
    """Open 2NT with 20-21 HCP and balanced shape.

    SAYC: "20-21 HCP, balanced."
    """

    @property
    def name(self) -> str:
        return "opening.2nt"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 270

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(20, 21), Balanced(strict=True))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="20-21 HCP, balanced — SAYC 2NT opening",
        )
