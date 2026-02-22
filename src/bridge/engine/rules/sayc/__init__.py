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
    RebidAccept2NTOver1NT,
    RebidAccept3MinorOver1NT,
    RebidAccept4NTOver1NT,
    RebidAcceptLimitRaiseMajor,
    RebidComplete2SPuppet,
    RebidCompleteTexas,
    RebidCompleteTransfer,
    RebidDecline2NTOver1NT,
    RebidDecline3MajorOver1NT,
    RebidDecline3MinorOver1NT,
    RebidDecline4NTOver1NT,
    RebidDeclineLimitRaise,
    RebidDoubleJumpRaiseResponder,
    RebidDoubleJumpRebidOwnSuit,
    RebidGameAfterRaiseMajor,
    RebidGerberResponse,
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
    RebidPassAfter3NTOver1NT,
    RebidPassAfterGameRaise,
    RebidPassAfterRaise,
    RebidPassOver1NT,
    RebidRaise2Over1Responder,
    RebidRaise3MajorOver1NT,
    RebidRaiseAfterJumpShift,
    RebidRaiseResponder,
    RebidReverse,
    RebidShowMajorAfter2NTMinor,
    RebidStayman2D,
    RebidStayman2H,
    RebidStayman2S,
    RebidSuitAfter2Over1,
    RebidSuitOver1NT,
    RebidSuperAccept,
)
from .response import (
    Respond1NTOverMajor,
    Respond1NTOverMinor,
    Respond2NTOver1NT,
    Respond2NTOverMinor,
    Respond2Over1,
    Respond2SPuppet,
    Respond3MajorOver1NT,
    Respond3MinorOver1NT,
    Respond3NTOver1NT,
    Respond3NTOverMajor,
    Respond3NTOverMinor,
    Respond4NTOver1NT,
    RespondGameRaiseMajor,
    RespondGerber,
    RespondJacoby2NT,
    RespondJacobyTransfer,
    RespondJumpShift,
    RespondLimitRaiseMajor,
    RespondLimitRaiseMinor,
    RespondNewSuit1Level,
    RespondPass,
    RespondPassOver1NT,
    RespondSingleRaiseMajor,
    RespondSingleRaiseMinor,
    RespondStayman,
    RespondTexasTransfer,
)


def create_sayc_registry() -> RuleRegistry:
    """Build a RuleRegistry with all SAYC bidding rules."""
    reg = RuleRegistry()
    # ── Opening bids ──────────────────────────────────────────────
    reg.register(Open2C())
    reg.register(Open2NT())
    reg.register(Open1NT())
    reg.register(OpenWeakTwo())
    reg.register(OpenPreempt4())
    reg.register(OpenPreempt3())
    reg.register(Open1Major())
    reg.register(Open1Minor())
    reg.register(OpenPass())

    # ── Responses to 1-of-a-suit ──────────────────────────────────
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

    # ── Responses to 1NT ─────────────────────────────────────────
    reg.register(RespondGerber())
    reg.register(Respond4NTOver1NT())
    reg.register(Respond3MajorOver1NT())
    reg.register(RespondTexasTransfer())
    reg.register(RespondStayman())
    reg.register(RespondJacobyTransfer())
    reg.register(Respond3NTOver1NT())
    reg.register(Respond3MinorOver1NT())
    reg.register(Respond2NTOver1NT())
    reg.register(Respond2SPuppet())
    reg.register(RespondPassOver1NT())

    # ── Opener rebids after jump shift ────────────────────────────
    reg.register(RebidRaiseAfterJumpShift())
    reg.register(RebidOwnSuitAfterJumpShift())
    reg.register(RebidNewSuitAfterJumpShift())
    reg.register(RebidNTAfterJumpShift())

    # ── Opener rebids after Jacoby 2NT ────────────────────────────
    reg.register(RebidJacoby3LevelShortness())
    reg.register(RebidJacoby4LevelSource())
    reg.register(RebidJacoby3Major())
    reg.register(RebidJacoby3NT())
    reg.register(RebidJacoby4Major())

    # ── Opener rebids after 3NT / 4M game raise ───────────────────
    reg.register(RebidPassAfter3NT())
    reg.register(RebidPassAfterGameRaise())

    # ── Opener rebids after 2NT over minor ────────────────────────
    reg.register(RebidShowMajorAfter2NTMinor())
    reg.register(RebidMinorAfter2NTMinor())
    reg.register(RebidNTAfter2NTMinor())

    # ── Opener rebids after limit raise ───────────────────────────
    reg.register(RebidAcceptLimitRaiseMajor())
    reg.register(Rebid5mAfterLimitRaiseMinor())
    reg.register(RebidDeclineLimitRaise())

    # ── Opener rebids after single raise ──────────────────────────
    reg.register(Rebid3NTAfterRaiseMinor())
    reg.register(RebidGameAfterRaiseMajor())
    reg.register(RebidInviteAfterRaiseMajor())
    reg.register(RebidHelpSuitGameTry())
    reg.register(Rebid2NTAfterRaiseMinor())
    reg.register(RebidNewSuitAfterRaiseMinor())
    reg.register(RebidPassAfterRaise())

    # ── Opener rebids after 1NT response ──────────────────────────
    reg.register(Rebid3NTOver1NT())
    reg.register(RebidJumpShiftOver1NT())
    reg.register(Rebid2NTOver1NT())
    reg.register(RebidJumpRebidOver1NT())
    reg.register(RebidNewLowerSuitOver1NT())
    reg.register(RebidSuitOver1NT())
    reg.register(RebidPassOver1NT())

    # ── Opener rebids after new suit at 1-level ───────────────────
    reg.register(RebidDoubleJumpRaiseResponder())
    reg.register(RebidDoubleJumpRebidOwnSuit())
    reg.register(RebidJumpTo2NT())
    reg.register(RebidJumpShiftNewSuit())
    reg.register(RebidJumpRaiseResponder())
    reg.register(RebidReverse())
    reg.register(RebidJumpRebidOwnSuit())
    reg.register(RebidRaiseResponder())
    reg.register(RebidNewSuitNonreverse())
    reg.register(RebidOwnSuit())  # also applies after 2-over-1
    reg.register(Rebid1NT())

    # ── Opener rebids after 2-over-1 ──────────────────────────────
    reg.register(RebidRaise2Over1Responder())
    reg.register(RebidNewSuitAfter2Over1())
    reg.register(Rebid3NTAfter2Over1())
    reg.register(RebidSuitAfter2Over1())
    reg.register(Rebid2NTAfter2Over1())

    # ── Opener rebids after 1NT opening (Stayman) ────────────────
    reg.register(RebidStayman2H())
    reg.register(RebidStayman2S())
    reg.register(RebidStayman2D())

    # ── Opener rebids after 1NT opening (transfers) ──────────────
    reg.register(RebidSuperAccept())
    reg.register(RebidCompleteTransfer())
    reg.register(RebidComplete2SPuppet())

    # ── Opener rebids after 1NT opening (conventions) ────────────
    reg.register(RebidGerberResponse())
    reg.register(RebidCompleteTexas())

    # ── Opener rebids after 1NT opening (raises/declines) ────────
    reg.register(RebidRaise3MajorOver1NT())
    reg.register(RebidDecline3MajorOver1NT())
    reg.register(RebidAccept2NTOver1NT())
    reg.register(RebidDecline2NTOver1NT())
    reg.register(RebidAccept3MinorOver1NT())
    reg.register(RebidDecline3MinorOver1NT())
    reg.register(RebidPassAfter3NTOver1NT())
    reg.register(RebidAccept4NTOver1NT())
    reg.register(RebidDecline4NTOver1NT())
    return reg
