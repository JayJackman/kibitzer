"""1-level suit opening bid rules — SAYC."""

from bridge.engine.condition import (
    All,
    Balanced,
    Computed,
    Condition,
    HcpRange,
    MeetsOpeningStrength,
    Not,
    TotalPtsRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.evaluate import best_major, best_minor
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

_not_1nt_range = Not(All(HcpRange(15, 17), Balanced(strict=True)), label="in 1NT range")
_not_2nt_range = Not(All(HcpRange(20, 21), Balanced(strict=True)), label="in 2NT range")
_not_2c_range = Not(TotalPtsRange(min_pts=22), label="in 2C range")


def _best_major(ctx: BiddingContext) -> Suit | None:
    return best_major(ctx.hand)


@condition("no 5+ card major")
def _no_major(ctx: BiddingContext) -> bool:
    return best_major(ctx.hand) is None


class Open1Major(Rule):
    """Open 1H or 1S with opening strength and a 5+ card major.

    SAYC: "12-21 HCP, 5+ card major. Five-card majors required in
    all seats."
    """

    def __init__(self) -> None:
        self._best_major = Computed(_best_major, "5+ card major")

    @property
    def name(self) -> str:
        return "opening.1_major"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 130

    @property
    def conditions(self) -> Condition:
        return All(
            MeetsOpeningStrength(),
            _not_1nt_range,
            _not_2nt_range,
            _not_2c_range,
            self._best_major,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._best_major.value
        return RuleResult(
            bid=SuitBid(1, suit),
            rule_name=self.name,
            explanation=f"5+ card {suit.letter}, opening strength — SAYC 1-major",
        )


class Open1Minor(Rule):
    """Open 1C or 1D with opening strength and no 5+ card major.

    SAYC: "1D requires 4+ diamonds (3 only with 4-4-3-2 shape:
    4S-4H-3D-2C). 1C requires 3+ clubs."

    Minor suit selection follows best_minor(): longer minor wins,
    4-4 opens 1D, 3-3 opens 1C.
    """

    @property
    def name(self) -> str:
        return "opening.1_minor"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 120

    @property
    def conditions(self) -> Condition:
        return All(
            MeetsOpeningStrength(),
            _not_1nt_range,
            _not_2nt_range,
            _not_2c_range,
            _no_major,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = best_minor(ctx.hand)
        return RuleResult(
            bid=SuitBid(1, suit),
            rule_name=self.name,
            explanation=(
                f"Opening strength, no 5+ major, best minor {suit.letter}"
                " — SAYC 1-minor"
            ),
        )


class OpenPass(Rule):
    """Pass when the hand does not meet any opening requirements.

    Fallback rule in the opening category.
    """

    @property
    def name(self) -> str:
        return "opening.pass"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 50

    def applies(self, ctx: BiddingContext) -> bool:
        return True

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Hand does not meet opening requirements",
        )
