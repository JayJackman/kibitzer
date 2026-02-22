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
from .rebid import (
    Rebid1NT,
    Rebid2NTAfter2Over1,
    Rebid2NTAfterRaiseMinor,
    Rebid2NTOver1NT,
    Rebid3NTAfter2Over1,
    Rebid3NTAfterRaiseMinor,
    Rebid3NTOver1NT,
    Rebid5mAfterLimitRaiseMinor,
    RebidAcceptLimitRaiseMajor,
    RebidDeclineLimitRaise,
    RebidDoubleJumpRaiseResponder,
    RebidDoubleJumpRebidOwnSuit,
    RebidGameAfterRaiseMajor,
    RebidHelpSuitGameTry,
    RebidInviteAfterRaiseMajor,
    RebidJacoby3LevelShortness,
    RebidJacoby3Major,
    RebidJacoby3NT,
    RebidJacoby4LevelSource,
    RebidJacoby4Major,
    RebidJumpRaiseResponder,
    RebidJumpRebidOver1NT,
    RebidJumpRebidOwnSuit,
    RebidJumpShiftNewSuit,
    RebidJumpShiftOver1NT,
    RebidJumpTo2NT,
    RebidMinorAfter2NTMinor,
    RebidNewLowerSuitOver1NT,
    RebidNewSuitAfter2Over1,
    RebidNewSuitAfterJumpShift,
    RebidNewSuitAfterRaiseMinor,
    RebidNewSuitNonreverse,
    RebidNTAfter2NTMinor,
    RebidNTAfterJumpShift,
    RebidOwnSuit,
    RebidOwnSuitAfterJumpShift,
    RebidPassAfter3NT,
    RebidPassAfterGameRaise,
    RebidPassAfterRaise,
    RebidPassOver1NT,
    RebidRaise2Over1Responder,
    RebidRaiseAfterJumpShift,
    RebidRaiseResponder,
    RebidReverse,
    RebidShowMajorAfter2NTMinor,
    RebidSuitAfter2Over1,
    RebidSuitOver1NT,
)
from .response import (
    Respond1NTOverMajor,
    Respond1NTOverMinor,
    Respond2NTOverMinor,
    Respond2Over1,
    Respond3NTOverMajor,
    Respond3NTOverMinor,
    RespondGameRaiseMajor,
    RespondJacoby2NT,
    RespondJumpShift,
    RespondLimitRaiseMajor,
    RespondLimitRaiseMinor,
    RespondNewSuit1Level,
    RespondPass,
    RespondSingleRaiseMajor,
    RespondSingleRaiseMinor,
)


def create_sayc_registry() -> RuleRegistry:
    """Build a RuleRegistry with all SAYC bidding rules."""
    reg = RuleRegistry()
    # Opening rules
    reg.register(Open2C())
    reg.register(Open2NT())
    reg.register(Open1NT())
    reg.register(OpenWeakTwo())
    reg.register(OpenPreempt4())
    reg.register(OpenPreempt3())
    reg.register(Open1Major())
    reg.register(Open1Minor())
    reg.register(OpenPass())
    # Response rules
    reg.register(RespondJumpShift())
    reg.register(RespondJacoby2NT())
    reg.register(RespondGameRaiseMajor())
    reg.register(Respond3NTOverMajor())
    reg.register(Respond3NTOverMinor())
    reg.register(Respond2NTOverMinor())
    reg.register(RespondLimitRaiseMajor())
    reg.register(RespondLimitRaiseMinor())
    reg.register(Respond2Over1())
    reg.register(RespondNewSuit1Level())
    reg.register(RespondSingleRaiseMajor())
    reg.register(RespondSingleRaiseMinor())
    reg.register(Respond1NTOverMinor())
    reg.register(Respond1NTOverMajor())
    reg.register(RespondPass())
    # Opener rebid rules — after jump shift (highest priority)
    reg.register(RebidRaiseAfterJumpShift())
    reg.register(RebidOwnSuitAfterJumpShift())
    reg.register(RebidNewSuitAfterJumpShift())
    reg.register(RebidNTAfterJumpShift())
    # Opener rebid rules — after Jacoby 2NT
    reg.register(RebidJacoby3LevelShortness())
    reg.register(RebidJacoby4LevelSource())
    reg.register(RebidJacoby3Major())
    reg.register(RebidJacoby3NT())
    reg.register(RebidJacoby4Major())
    # Opener rebid rules — after 2NT over minor
    reg.register(RebidShowMajorAfter2NTMinor())
    reg.register(RebidMinorAfter2NTMinor())
    reg.register(RebidNTAfter2NTMinor())
    # Opener rebid rules — after new suit 1-level (double-jumps)
    reg.register(RebidDoubleJumpRaiseResponder())
    reg.register(RebidDoubleJumpRebidOwnSuit())
    # Opener rebid rules — existing (after new suit 1-level)
    reg.register(RebidJumpTo2NT())
    reg.register(RebidJumpShiftNewSuit())
    reg.register(Rebid3NTOver1NT())
    reg.register(RebidJumpShiftOver1NT())
    reg.register(Rebid3NTAfterRaiseMinor())
    reg.register(RebidAcceptLimitRaiseMajor())
    reg.register(RebidGameAfterRaiseMajor())
    reg.register(RebidRaise2Over1Responder())
    reg.register(RebidJumpRaiseResponder())
    reg.register(RebidNewSuitAfter2Over1())
    reg.register(RebidReverse())
    reg.register(Rebid2NTOver1NT())
    reg.register(RebidJumpRebidOwnSuit())
    reg.register(RebidJumpRebidOver1NT())
    reg.register(RebidInviteAfterRaiseMajor())
    reg.register(RebidHelpSuitGameTry())
    reg.register(Rebid2NTAfterRaiseMinor())
    reg.register(Rebid3NTAfter2Over1())
    reg.register(RebidSuitAfter2Over1())
    reg.register(Rebid5mAfterLimitRaiseMinor())
    reg.register(RebidNewSuitAfterRaiseMinor())
    reg.register(RebidRaiseResponder())
    reg.register(RebidNewLowerSuitOver1NT())
    reg.register(RebidNewSuitNonreverse())
    reg.register(RebidSuitOver1NT())
    reg.register(RebidOwnSuit())
    reg.register(Rebid2NTAfter2Over1())
    reg.register(Rebid1NT())
    reg.register(RebidDeclineLimitRaise())
    reg.register(RebidPassAfterRaise())
    reg.register(RebidPassAfterGameRaise())
    reg.register(RebidPassAfter3NT())
    reg.register(RebidPassOver1NT())
    return reg
