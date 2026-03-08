"""Bidding engine — rule-based bid selection."""

from .context import AuctionContext, BiddingContext
from .query import BidAnalysis, RuleMatch, analyze_bid
from .registry import DuplicateRuleError, RuleRegistry
from .rule import Category, Rule, RuleResult
from .selector import BidSelector

__all__ = [
    "AuctionContext",
    "BidAnalysis",
    "BidSelector",
    "BiddingContext",
    "Category",
    "DuplicateRuleError",
    "Rule",
    "RuleMatch",
    "RuleRegistry",
    "RuleResult",
    "analyze_bid",
]
