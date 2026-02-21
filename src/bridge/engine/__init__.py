"""Bidding engine — rule-based bid selection."""

from .context import BiddingContext
from .registry import DuplicateRuleError, RuleRegistry
from .rule import Category, Rule, RuleResult
from .selector import BidSelector

__all__ = [
    "BidSelector",
    "BiddingContext",
    "Category",
    "DuplicateRuleError",
    "Rule",
    "RuleRegistry",
    "RuleResult",
]
