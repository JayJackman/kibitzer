"""BidSelector — phase detection and priority-based rule resolution."""

from __future__ import annotations

from bridge.engine.context import BiddingContext
from bridge.engine.registry import RuleRegistry
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS

# Overlay categories are always checked alongside the detected phase.
_OVERLAY_CATEGORIES = (Category.CONVENTION, Category.SLAM)


class BidSelector:
    """Selects the best bid by detecting the auction phase and applying rules."""

    def __init__(self, registry: RuleRegistry) -> None:
        self._registry = registry

    def detect_phase(self, ctx: BiddingContext) -> Category:
        """Determine which rule category to search based on auction state."""
        if not ctx.has_opened:
            return Category.OPENING

        opening = ctx.opening_bid
        assert opening is not None  # has_opened guarantees this

        opening_seat = opening[0]
        partner = ctx.seat.partner
        my_side = {ctx.seat, partner}
        opener_is_my_side = opening_seat in my_side

        if opener_is_my_side:
            if opening_seat == partner:
                # Partner opened
                if ctx.is_my_first_bid:
                    if ctx.is_competitive:
                        return Category.COMPETITIVE_RESPONSE
                    return Category.RESPONSE
                return Category.REBID_RESPONDER
            # I opened
            return Category.REBID_OPENER

        # Opponent opened
        return Category.COMPETITIVE

    def select(self, ctx: BiddingContext) -> RuleResult:
        """Pick the highest-priority matching rule and return its result.

        Falls back to Pass if no rule applies.
        """
        candidates = self._collect_rules(ctx)

        for rule in candidates:
            if rule.applies(ctx):
                return rule.select(ctx)

        return RuleResult(
            bid=PASS,
            rule_name="fallback.pass",
            explanation="No applicable rule",
        )

    def candidates(self, ctx: BiddingContext) -> list[RuleResult]:
        """All matching rule results, not just the winner.

        Useful for the LLM layer to explain what was considered.
        """
        rules = self._collect_rules(ctx)
        return [rule.select(ctx) for rule in rules if rule.applies(ctx)]

    def _collect_rules(self, ctx: BiddingContext) -> list[Rule]:
        """Gather phase rules + overlay rules, sorted by priority descending."""
        phase = self.detect_phase(ctx)
        rules: list[Rule] = list(self._registry.rules_for(phase))
        for overlay in _OVERLAY_CATEGORIES:
            rules.extend(self._registry.rules_for(overlay))
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules
