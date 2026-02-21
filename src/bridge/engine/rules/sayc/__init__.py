"""SAYC bidding system — all rules wired into a RuleRegistry."""

from bridge.engine.registry import RuleRegistry

from .opening import (
    Open1Major,
    Open1Minor,
    Open1NT,
    Open2C,
    Open2NT,
    OpenPass,
    OpenPreempt3,
    OpenPreempt4,
    OpenWeakTwo,
)


def create_sayc_registry() -> RuleRegistry:
    """Build a RuleRegistry with all SAYC bidding rules.

    As more phases are completed (response, rebid, etc.),
    this function grows to include all SAYC rules.
    """
    reg = RuleRegistry()
    reg.register(Open2C())
    reg.register(Open2NT())
    reg.register(Open1NT())
    reg.register(OpenWeakTwo())
    reg.register(OpenPreempt4())
    reg.register(OpenPreempt3())
    reg.register(Open1Major())
    reg.register(Open1Minor())
    reg.register(OpenPass())
    return reg
