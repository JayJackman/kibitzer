"""RuleRegistry — collects and indexes bidding rules."""

from __future__ import annotations

from bridge.engine.rule import Category, Rule


class DuplicateRuleError(Exception):
    """Raised when registering a rule with a duplicate name or priority."""


class RuleRegistry:
    """Collects rules and indexes them by category for fast lookup."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}
        self._by_category: dict[Category, list[Rule]] = {}

    def register(self, rule: Rule) -> None:
        """Add a rule to the registry.

        Raises DuplicateRuleError if a rule with the same name already exists,
        or if a rule with the same priority already exists in the same category.
        """
        if rule.name in self._rules:
            raise DuplicateRuleError(f"Duplicate rule name: {rule.name!r}")

        category_rules = self._by_category.get(rule.category, [])
        for existing in category_rules:
            if existing.priority == rule.priority:
                raise DuplicateRuleError(
                    f"Duplicate priority {rule.priority} in category "
                    f"{rule.category!r}: {existing.name!r} and {rule.name!r}"
                )

        self._rules[rule.name] = rule
        self._by_category.setdefault(rule.category, []).append(rule)

    def rules_for(self, category: Category) -> list[Rule]:
        """Rules for a category, sorted by priority descending (highest first)."""
        return sorted(
            self._by_category.get(category, []),
            key=lambda r: r.priority,
            reverse=True,
        )

    def all_rules(self) -> list[Rule]:
        """All registered rules, sorted by priority descending."""
        return sorted(
            self._rules.values(),
            key=lambda r: r.priority,
            reverse=True,
        )
