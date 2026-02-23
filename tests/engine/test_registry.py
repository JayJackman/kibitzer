"""Tests for RuleRegistry."""

import pytest

from bridge.engine.condition import Condition, condition
from bridge.engine.context import BiddingContext
from bridge.engine.registry import DuplicateRuleError, RuleRegistry
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, Bid


@condition("always")
def _always(ctx: BiddingContext) -> bool:
    return True


@condition("never")
def _never(ctx: BiddingContext) -> bool:
    return False


class MockRule(Rule):
    """Configurable mock rule for testing the registry."""

    def __init__(
        self,
        name: str,
        category: Category,
        priority: int,
        bid: Bid | None = None,
        should_apply: bool = True,
    ) -> None:
        self._name = name
        self._category = category
        self._priority = priority
        self._bid = bid or PASS
        self._should_apply = should_apply

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> Category:
        return self._category

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def conditions(self) -> Condition:
        return _always if self._should_apply else _never

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=self._bid,
            rule_name=self._name,
            explanation=f"Mock rule {self._name}",
        )


class TestRuleRegistry:
    def test_register_and_lookup(self) -> None:
        reg = RuleRegistry()
        rule = MockRule("opening.1nt", Category.OPENING, 200)
        reg.register(rule)

        rules = reg.rules_for(Category.OPENING)
        assert len(rules) == 1
        assert rules[0].name == "opening.1nt"

    def test_empty_category(self) -> None:
        reg = RuleRegistry()
        assert reg.rules_for(Category.OPENING) == []

    def test_priority_ordering(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1suit", Category.OPENING, 100))
        reg.register(MockRule("opening.1nt", Category.OPENING, 200))
        reg.register(MockRule("opening.2c", Category.OPENING, 400))

        rules = reg.rules_for(Category.OPENING)
        assert [r.name for r in rules] == [
            "opening.2c",
            "opening.1nt",
            "opening.1suit",
        ]

    def test_duplicate_name_rejected(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1nt", Category.OPENING, 200))

        with pytest.raises(DuplicateRuleError, match="Duplicate rule name"):
            reg.register(MockRule("opening.1nt", Category.OPENING, 201))

    def test_duplicate_priority_in_category_rejected(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1nt", Category.OPENING, 200))

        with pytest.raises(DuplicateRuleError, match="Duplicate priority 200"):
            reg.register(MockRule("opening.2nt", Category.OPENING, 200))

    def test_same_priority_different_categories_ok(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1nt", Category.OPENING, 200))
        reg.register(MockRule("response.1nt", Category.RESPONSE, 200))

        assert len(reg.rules_for(Category.OPENING)) == 1
        assert len(reg.rules_for(Category.RESPONSE)) == 1

    def test_all_rules(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1suit", Category.OPENING, 100))
        reg.register(MockRule("response.raise", Category.RESPONSE, 150))
        reg.register(MockRule("opening.2c", Category.OPENING, 400))

        all_rules = reg.all_rules()
        assert len(all_rules) == 3
        assert [r.name for r in all_rules] == [
            "opening.2c",
            "response.raise",
            "opening.1suit",
        ]

    def test_multiple_categories(self) -> None:
        reg = RuleRegistry()
        reg.register(MockRule("opening.1nt", Category.OPENING, 200))
        reg.register(MockRule("opening.1suit", Category.OPENING, 100))
        reg.register(MockRule("response.raise", Category.RESPONSE, 150))

        assert len(reg.rules_for(Category.OPENING)) == 2
        assert len(reg.rules_for(Category.RESPONSE)) == 1
        assert len(reg.rules_for(Category.COMPETITIVE)) == 0
