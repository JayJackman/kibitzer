"""1-level suit opening bid rules — SAYC."""

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.evaluate import best_major, best_minor, rule_of_15, rule_of_20
from bridge.model.bid import PASS, SuitBid


def _meets_opening_strength(ctx: BiddingContext) -> bool:
    """Whether the hand meets opening strength for 1-level suit bids.

    - 1st/2nd/3rd seat: hcp >= 12 or Rule of 20.
    - 4th seat: Rule of 15 (HCP + spades >= 15).
    """
    seat_offset = (ctx.seat.value - ctx.auction.dealer.value) % 4
    if seat_offset == 3:
        return rule_of_15(ctx.hand, ctx.hcp)
    return ctx.hcp >= 12 or rule_of_20(ctx.hand, ctx.hcp)


class Open1Major(Rule):
    """Open 1H or 1S with opening strength and a 5+ card major.

    SAYC: "12-21 HCP, 5+ card major. Five-card majors required in
    all seats."
    """

    @property
    def name(self) -> str:
        return "opening.1_major"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 130

    def applies(self, ctx: BiddingContext) -> bool:
        if not _meets_opening_strength(ctx):
            return False
        if ctx.is_balanced and 15 <= ctx.hcp <= 17:
            return False
        if ctx.is_balanced and 20 <= ctx.hcp <= 21:
            return False
        if ctx.total_pts >= 22:
            return False
        return best_major(ctx.hand) is not None

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = best_major(ctx.hand)
        assert suit is not None
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _meets_opening_strength(ctx):
            return False
        if ctx.is_balanced and 15 <= ctx.hcp <= 17:
            return False
        if ctx.is_balanced and 20 <= ctx.hcp <= 21:
            return False
        if ctx.total_pts >= 22:
            return False
        return best_major(ctx.hand) is None

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
