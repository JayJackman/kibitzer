"""BidSelector — phase detection and priority-based rule resolution."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bridge.engine.condition import ConditionResult
from bridge.engine.context import BiddingContext
from bridge.engine.registry import RuleRegistry
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, Bid

logger = logging.getLogger(__name__)

# Overlay categories are always checked alongside the detected phase.
_OVERLAY_CATEGORIES = (Category.CONVENTION, Category.SLAM)


class AmbiguousBidError(Exception):
    """Two rules at the same priority both matched — a real conflict."""


@dataclass(frozen=True)
class ThoughtStep:
    """One rule evaluated during the thought process."""

    rule_name: str
    passed: bool
    bid: Bid | None
    condition_results: tuple[ConditionResult, ...]


@dataclass(frozen=True)
class ThoughtProcess:
    """Full trace of how the engine reached its decision."""

    steps: tuple[ThoughtStep, ...]
    selected: RuleResult


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

        Raises ``AmbiguousBidError`` if two rules at the same priority both
        match.  Falls back to Pass if no rule applies.
        """
        candidates = self._collect_rules(ctx)
        phase = self.detect_phase(ctx)
        logger.debug("Phase: %s, evaluating %d rules", phase.name, len(candidates))

        for i, rule in enumerate(candidates):
            if rule.applies(ctx):
                # Check for same-priority ambiguity.
                for other in candidates[i + 1 :]:
                    if other.priority != rule.priority:
                        break
                    if other.applies(ctx):
                        raise AmbiguousBidError(
                            f"Rules {rule.name!r} and {other.name!r} both "
                            f"match at priority {rule.priority}"
                        )
                result = rule.select(ctx)
                logger.debug("Rule %s matched -> %s", rule.name, result.bid)
                return result

        logger.debug("No rule matched, falling back to Pass")
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

    def think(self, ctx: BiddingContext) -> ThoughtProcess:
        """Evaluate all candidate rules and produce a structured trace.

        Raises ``AmbiguousBidError`` if two rules at the same priority both
        match.
        """
        rules = self._collect_rules(ctx)
        steps: list[ThoughtStep] = []
        winner: RuleResult | None = None
        winner_rule: Rule | None = None

        for rule in rules:
            check_result = rule.check(ctx)
            passed = check_result.passed
            result = rule.select(ctx) if passed else None
            logger.debug("Rule %s: %s", rule.name, "PASS" if passed else "fail")
            steps.append(
                ThoughtStep(
                    rule_name=rule.name,
                    passed=passed,
                    bid=result.bid if result else None,
                    condition_results=check_result.results,
                )
            )
            if passed and winner is None:
                winner = result
                winner_rule = rule
            elif (
                passed
                and winner_rule is not None
                and rule.priority == winner_rule.priority
            ):
                raise AmbiguousBidError(
                    f"Rules {winner_rule.name!r} and {rule.name!r} both "
                    f"match at priority {rule.priority}"
                )

        if winner is None:
            winner = RuleResult(
                bid=PASS,
                rule_name="fallback.pass",
                explanation="No rule matched",
            )

        return ThoughtProcess(steps=tuple(steps), selected=winner)

    def _collect_rules(self, ctx: BiddingContext) -> list[Rule]:
        """Gather phase rules + overlay rules, sorted by priority descending."""
        phase = self.detect_phase(ctx)
        rules: list[Rule] = list(self._registry.rules_for(phase))
        for overlay in _OVERLAY_CATEGORIES:
            rules.extend(self._registry.rules_for(overlay))
        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules
