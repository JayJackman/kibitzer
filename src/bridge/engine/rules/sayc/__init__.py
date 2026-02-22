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
    Rebid2NTAccept4NT,
    Rebid2NTAfter2C,
    Rebid2NTAfter2Over1,
    Rebid2NTAfterRaiseMinor,
    Rebid2NTComplete3SPuppet,
    Rebid2NTCompleteTexas,
    Rebid2NTCompleteTransfer,
    Rebid2NTDecline4NT,
    Rebid2NTGerberResponse,
    Rebid2NTOver1NT,
    Rebid2NTPassAfter3NT,
    Rebid2NTStayman3D,
    Rebid2NTStayman3H,
    Rebid2NTStayman3S,
    Rebid3NTAfter2C,
    Rebid3NTAfter2Over1,
    Rebid3NTAfterFeatureAsk,
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
    RebidNTAfterPositive2C,
    RebidOwnSuit,
    RebidOwnSuitAfterFeatureAsk,
    RebidOwnSuitAfterJumpShift,
    RebidOwnSuitAfterNewSuit3Level,
    RebidOwnSuitAfterNewSuitWeakTwo,
    RebidPassAfter3Level,
    RebidPassAfter3NT,
    RebidPassAfter3NTOver1NT,
    RebidPassAfter4Level,
    RebidPassAfterGameRaise,
    RebidPassAfterRaise,
    RebidPassAfterWeakTwo,
    RebidPassOver1NT,
    RebidRaise2Over1Responder,
    RebidRaise3MajorOver1NT,
    RebidRaiseAfterJumpShift,
    RebidRaiseAfterNewSuit3Level,
    RebidRaiseAfterPositive2C,
    RebidRaiseNewSuitWeakTwo,
    RebidRaiseResponder,
    RebidReverse,
    RebidShowFeature,
    RebidShowMajorAfter2NTMinor,
    RebidStayman2D,
    RebidStayman2H,
    RebidStayman2S,
    RebidSuitAfter2C,
    RebidSuitAfter2Over1,
    RebidSuitAfterPositive2C,
    RebidSuitOver1NT,
    RebidSuperAccept,
)
from .response import (
    Respond1NTOverMajor,
    Respond1NTOverMinor,
    Respond2DWaiting,
    Respond2NTFeatureAsk,
    Respond2NTOver1NT,
    Respond2NTOver2C,
    Respond2NTOverMinor,
    Respond2Over1,
    Respond2SPuppet,
    Respond3MajorOver1NT,
    Respond3MinorOver1NT,
    Respond3NTOver1NT,
    Respond3NTOver2NT,
    Respond3NTOver3Level,
    Respond3NTOverMajor,
    Respond3NTOverMinor,
    Respond3NTOverWeakTwo,
    Respond3SPuppetOver2NT,
    Respond4NTOver1NT,
    Respond4NTOver2NT,
    RespondGameRaise3Level,
    RespondGameRaiseMajor,
    RespondGameRaiseWeakTwo,
    RespondGerber,
    RespondGerberOver2NT,
    RespondJacoby2NT,
    RespondJacobyTransfer,
    RespondJumpShift,
    RespondLimitRaiseMajor,
    RespondLimitRaiseMinor,
    RespondNewSuit1Level,
    RespondNewSuitOver3Level,
    RespondNewSuitOverWeakTwo,
    RespondPass,
    RespondPassOver1NT,
    RespondPassOver2NT,
    RespondPassOver3Level,
    RespondPassOver4Level,
    RespondPassOverWeakTwo,
    RespondPositiveSuitOver2C,
    RespondRaise3Level,
    RespondRaise4Level,
    RespondRaiseWeakTwo,
    RespondSingleRaiseMajor,
    RespondSingleRaiseMinor,
    RespondStayman,
    RespondStaymanOver2NT,
    RespondTexasOver2NT,
    RespondTexasTransfer,
    RespondTransferOver2NT,
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

    # ── Responses to 2C ──────────────────────────────────────────────
    reg.register(Respond2NTOver2C())
    reg.register(RespondPositiveSuitOver2C())
    reg.register(Respond2DWaiting())

    # ── Opener rebids after 2C opening (after 2D waiting) ────────────
    reg.register(Rebid2NTAfter2C())
    reg.register(Rebid3NTAfter2C())
    reg.register(RebidSuitAfter2C())

    # ── Opener rebids after 2C opening (after positive response) ─────
    reg.register(RebidRaiseAfterPositive2C())
    reg.register(RebidSuitAfterPositive2C())
    reg.register(RebidNTAfterPositive2C())

    # ── Responses to 2NT ────────────────────────────────────────────
    reg.register(RespondGerberOver2NT())
    reg.register(Respond4NTOver2NT())
    reg.register(RespondTexasOver2NT())
    reg.register(RespondStaymanOver2NT())
    reg.register(RespondTransferOver2NT())
    reg.register(Respond3NTOver2NT())
    reg.register(Respond3SPuppetOver2NT())
    reg.register(RespondPassOver2NT())

    # ── Opener rebids after 2NT opening (Stayman) ──────────────────
    reg.register(Rebid2NTStayman3H())
    reg.register(Rebid2NTStayman3S())
    reg.register(Rebid2NTStayman3D())

    # ── Opener rebids after 2NT opening (transfers) ────────────────
    reg.register(Rebid2NTCompleteTransfer())
    reg.register(Rebid2NTComplete3SPuppet())

    # ── Opener rebids after 2NT opening (conventions) ──────────────
    reg.register(Rebid2NTGerberResponse())
    reg.register(Rebid2NTCompleteTexas())

    # ── Opener rebids after 2NT opening (raises/declines) ──────────
    reg.register(Rebid2NTPassAfter3NT())
    reg.register(Rebid2NTAccept4NT())
    reg.register(Rebid2NTDecline4NT())

    # ── Responses to weak two (2D/2H/2S) ────────────────────────────
    reg.register(RespondGameRaiseWeakTwo())
    reg.register(Respond3NTOverWeakTwo())
    reg.register(RespondNewSuitOverWeakTwo())
    reg.register(Respond2NTFeatureAsk())
    reg.register(RespondRaiseWeakTwo())
    reg.register(RespondPassOverWeakTwo())

    # ── Responses to 3-level preempt ─────────────────────────────────
    reg.register(RespondGameRaise3Level())
    reg.register(Respond3NTOver3Level())
    reg.register(RespondNewSuitOver3Level())
    reg.register(RespondRaise3Level())
    reg.register(RespondPassOver3Level())

    # ── Responses to 4-level preempt ─────────────────────────────────
    reg.register(RespondRaise4Level())
    reg.register(RespondPassOver4Level())

    # ── Opener rebids after weak two ─────────────────────────────────
    reg.register(RebidShowFeature())
    reg.register(Rebid3NTAfterFeatureAsk())
    reg.register(RebidOwnSuitAfterFeatureAsk())
    reg.register(RebidRaiseNewSuitWeakTwo())
    reg.register(RebidOwnSuitAfterNewSuitWeakTwo())
    reg.register(RebidPassAfterWeakTwo())

    # ── Opener rebids after 3-level preempt ──────────────────────────
    reg.register(RebidRaiseAfterNewSuit3Level())
    reg.register(RebidOwnSuitAfterNewSuit3Level())
    reg.register(RebidPassAfter3Level())

    # ── Opener rebids after 4-level preempt ──────────────────────────
    reg.register(RebidPassAfter4Level())
    return reg
