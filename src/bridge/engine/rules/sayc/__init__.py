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
    Rebid2NTAfter2COffshape,
    Rebid2NTAfter2Over1,
    Rebid2NTAfterRaiseMinor,
    Rebid2NTComplete3SPuppet,
    Rebid2NTCompleteTexas,
    Rebid2NTCompleteTransfer,
    Rebid2NTDecline4NT,
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
    RebidAcceptLimitRaiseMinor3NT,
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
    RebidGameAfterSingleRaiseMinor,
    RebidGameOver1NT,
    RebidGerber0or4Aces,
    RebidGerber1Ace,
    RebidGerber2Aces,
    RebidGerber3Aces,
    RebidHelpSuitGameTry,
    RebidInviteAfterRaiseMajor,
    RebidInviteAfterRaiseMinor,
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
    RebidOwnSuit5Card,
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
    RebidSuitOver1NT5Card,
    RebidSuperAccept,
)
from .reresponse import (
    # Suit opening
    Accept2NTAfterMinorRaise,
    Accept3yJumpRaise,
    Accept3yJumpRaise3NT,
    AcceptGameTry,
    AcceptMinorInvite,
    AcceptQuantitative4NTMinor,
    AcceptReraise,
    Bid4MAfter3NTMedium,
    Bid4MAfterMax,
    Bid4MAfterShortness,
    Bid4MAfterSource,
    Blackwood4NTAfter3NTMedium,
    Blackwood4NTAfterJacoby4M,
    Blackwood4NTAfterJS,
    Blackwood4NTAfterMax,
    Blackwood4NTAfterShortness,
    Blackwood4NTAfterSource,
    BlackwoodResponseAfterLimitRaise,
    # NT opening (Puppet)
    CorrectPuppet2NTDiamonds,
    CorrectPuppetDiamonds,
    Decline2NTAfterMinorRaise,
    Decline3yJumpRaise,
    DeclineGameTry,
    DeclineMinorInvite,
    DeclineQuantitative4NTMinor,
    DeclineReraise,
    FourMAfter1NTRebid,
    FourMAfter2NTRebid,
    FourMAfter2Over1NewSuit,
    FourMAfter2Over1OwnSuit,
    FourMAfterJS,
    FourMAfterJumpRebid,
    FourMAfterJumpRebidOver1NT,
    FourMAfterNewSuit,
    FourMAfterOwnSuitMajor,
    FourMAfterRaise,
    FourMAfterRaise2Over1,
    FourthSuitAfter2Over1NS,
    FourthSuitAfterOwnSuit,
    FourthSuitForcing,
    # NT opening (Stayman)
    Game3NT2NTDenial,
    Game3NT2NTNoFit,
    Game3NTAfterDenial,
    # NT opening (Transfers)
    Game3NTAfterTransfer,
    Game3NTStaymanNoFit,
    Game3NTSuperAccept,
    Game3NTTransfer2NT,
    Game4MSuperAccept,
    Game4MTransfer2NT,
    GameInMinorAfterRaise,
    GameRaise2NTStaymanFit,
    GameRaiseStaymanFit,
    GameRaiseTransfer,
    GFAfterReverse,
    GFMajor2NTDenial,
    GFMajorAfterDenial,
    GFMajors55,
    GFRaiseReverseSuit,
    Invite2NTAfterDenial,
    Invite2NTAfterTransfer,
    Invite2NTStaymanNoFit,
    InviteMajorAfterDenial,
    InviteMajors55,
    InviteRaiseStaymanFit,
    InviteRaiseTransfer,
    JumpInOwnSuitAfterReverse,
    JumpOwnMajorAfter1NT,
    JumpRebidAfter1NT,
    JumpRebidOwnSuitAfterNewSuit,
    JumpRebidOwnSuitAfterOwnSuit,
    # NT opening (Gerber)
    KingAskAfterGerber,
    NewSuitAfter1NTForcing,
    NewSuitAfter2Over1OwnSuit,
    NewSuitAt1Level,
    NewSuitForcingAfterMinorRaise,
    NewSuitForcingAfterOwnSuit,
    NewSuitWeakAfter1NT,
    OneNTReresponse,
    PassAfter1NTRebid,
    PassAfter2NTMinor3NT,
    PassAfter2NTOver1NT,
    PassAfter2NTRebid,
    PassAfter2Over1_2NT,
    PassAfter3NT2Over1,
    PassAfter3NTOver1NT,
    PassAfter3NTRebid,
    PassAfter3NTResponse,
    PassAfterAcceptedLimitRaise,
    PassAfterDoubleJumpRaise,
    PassAfterDoubleJumpRebid,
    PassAfterGame,
    PassAfterGameJumpOver1NT,
    PassAfterGerber,
    PassAfterJacoby4M,
    PassAfterJumpRebid,
    PassAfterJumpRebidOver1NT,
    PassAfterMinor3NT,
    PassAfterMinorGame,
    PassAfterMinorRaise2Over1,
    PassAfterNewSuit,
    PassAfterNewSuit1NT,
    # NT opening (Signoff)
    PassAfterNTReresponse,
    PassAfterRaise,
    PassAfterSuitRebid1NT,
    PassAfterTexas,
    PassGarbageStayman,
    PassGarbageStaymanFit,
    PassPuppet2NTClubs,
    PassPuppetClubs,
    PassSuperAccept,
    PassTransfer2NTSignoff,
    PassTransferSignoff,
    PreferenceAfter2Over1NS,
    PreferenceAfterOwnSuit,
    PreferenceAfterReverse,
    PreferenceAfterReverse2Over1,
    PreferenceAfterReverseOver1NT,
    PreferenceTo1stSuit1NT,
    PreferenceToOpenerFirst,
    Quant4NT2NTDenial,
    Quant4NT2NTStaymanFit,
    Quant4NTSuperAccept,
    Quant4NTTransfer2NT,
    Raise2ndSuitAfterMinorRaise,
    RaiseJumpShiftSuit,
    RaiseNewSuit1NTResponse,
    RaiseNewSuitInvite,
    RaiseOpenerAfter2Over1,
    RaiseOpenerNewSuit2Over1,
    RaiseReverseSuit,
    RaiseReverseSuit2Over1,
    RaiseReverseSuitOver1NT,
    RebidOwnAfter2Over1NS,
    RebidOwnAfterReverse2Over1,
    RebidOwnSuitAfter1NT,
    RebidOwnSuitAfter2Over1,
    RebidOwnSuitAfterJS,
    RebidOwnSuitAfterNewSuit,
    RebidOwnSuitAfterOwnSuit,
    RebidOwnSuitAfterReverse,
    ReturnToMinor,
    ReturnToOpenerSuitAfterJS1NT,
    ShowSecondSuitAfterJS,
    SignoffAfterGerber,
    SlamMinor2NTDenial,
    SlamMinorAfterDenial,
    SlamTryMinorAfterRaise,
    SupportJumpShiftOver1NT,
    SupportOpenerFirstAfterJS,
    ThreeNTAfter1NTRebid,
    ThreeNTAfter2NTMinorMajor,
    ThreeNTAfter2NTMinorRebid,
    ThreeNTAfter2NTOver1NT,
    ThreeNTAfter2NTRebid,
    ThreeNTAfter2Over1_2NT,
    ThreeNTAfter2Over1NewSuit,
    ThreeNTAfter2Over1OwnSuit,
    ThreeNTAfterJSOver1NT,
    ThreeNTAfterJSReresponse,
    ThreeNTAfterJumpRebid,
    ThreeNTAfterJumpRebidNoStoppers,
    ThreeNTAfterJumpRebidOver1NT,
    ThreeNTAfterJumpShift,
    ThreeNTAfterMinorNewSuit,
    ThreeNTAfterNewSuit,
    ThreeNTAfterOwnSuit,
    ThreeNTAfterRaise,
    ThreeNTAfterRaise2Over1,
    ThreeNTAfterReverse,
    ThreeNTAfterReverse2Over1,
    ThreeNTAfterReverseOver1NT,
    ThreeSuitAfter2NTRebid,
    ThreeSuitAfter2Over1_2NT,
    ThreeXInviteAfterOwnSuit,
    ThreeYInviteAfterRaise,
    TwoNTAfter1NTRebid,
    TwoNTAfter2Over1,
    TwoNTAfter2Over1NS,
    TwoNTAfterNewSuit,
    TwoNTAfterOwnSuit,
    TwoNTAfterReverse,
    TwoNTAfterReverse2Over1,
    TwoNTAfterReverseOver1NT,
    WeakRaiseNewSuit,
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
    RespondGameRaise3LevelMajor,
    RespondGameRaise3LevelMinor,
    RespondGameRaiseMajor,
    RespondGameRaiseWeakTwoMajor,
    RespondGameRaiseWeakTwoMinor,
    RespondGerber,
    RespondGerberOver2NT,
    RespondJacoby2NT,
    RespondJacobyTransferHearts,
    RespondJacobyTransferSpades,
    RespondJumpShift,
    RespondLimitRaiseClubs,
    RespondLimitRaiseDiamonds,
    RespondLimitRaiseMajor,
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
    RespondSingleRaiseClubs,
    RespondSingleRaiseDiamonds,
    RespondSingleRaiseMajor,
    RespondStayman,
    RespondStaymanOver2NT,
    RespondTexasOver2NT,
    RespondTexasTransfer,
    RespondTransferHeartsOver2NT,
    RespondTransferSpadesOver2NT,
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
    reg.register(RespondLimitRaiseDiamonds())
    reg.register(RespondLimitRaiseClubs())
    reg.register(Respond2Over1())
    reg.register(RespondNewSuit1Level())
    reg.register(RespondSingleRaiseMajor())
    reg.register(RespondSingleRaiseDiamonds())
    reg.register(RespondSingleRaiseClubs())
    reg.register(Respond1NTOverMinor())
    reg.register(Respond1NTOverMajor())
    reg.register(RespondPass())

    # ── Responses to 1NT ─────────────────────────────────────────
    reg.register(RespondGerber())
    reg.register(Respond4NTOver1NT())
    reg.register(Respond3MajorOver1NT())
    reg.register(RespondTexasTransfer())
    reg.register(RespondStayman())
    reg.register(RespondJacobyTransferHearts())
    reg.register(RespondJacobyTransferSpades())
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
    reg.register(RebidAcceptLimitRaiseMinor3NT())
    reg.register(RebidDeclineLimitRaise())

    # ── Opener rebids after single raise ──────────────────────────
    reg.register(Rebid3NTAfterRaiseMinor())
    reg.register(RebidGameAfterRaiseMajor())
    reg.register(RebidGameAfterSingleRaiseMinor())
    reg.register(RebidInviteAfterRaiseMajor())
    reg.register(RebidInviteAfterRaiseMinor())
    reg.register(RebidHelpSuitGameTry())
    reg.register(Rebid2NTAfterRaiseMinor())
    reg.register(RebidNewSuitAfterRaiseMinor())
    reg.register(RebidPassAfterRaise())

    # ── Opener rebids after 1NT response ──────────────────────────
    reg.register(Rebid3NTOver1NT())
    reg.register(RebidGameOver1NT())
    reg.register(RebidJumpShiftOver1NT())
    reg.register(Rebid2NTOver1NT())
    reg.register(RebidJumpRebidOver1NT())
    reg.register(RebidNewLowerSuitOver1NT())
    reg.register(RebidSuitOver1NT())
    reg.register(RebidSuitOver1NT5Card())
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
    reg.register(RebidOwnSuit5Card())  # 5-card fallback, also after 2-over-1
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
    reg.register(RebidGerber0or4Aces())
    reg.register(RebidGerber1Ace())
    reg.register(RebidGerber2Aces())
    reg.register(RebidGerber3Aces())
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
    reg.register(Rebid2NTAfter2COffshape())

    # ── Opener rebids after 2C opening (after positive response) ─────
    reg.register(RebidRaiseAfterPositive2C())
    reg.register(RebidSuitAfterPositive2C())
    reg.register(RebidNTAfterPositive2C())

    # ── Responses to 2NT ────────────────────────────────────────────
    reg.register(RespondGerberOver2NT())
    reg.register(Respond4NTOver2NT())
    reg.register(RespondTexasOver2NT())
    reg.register(RespondStaymanOver2NT())
    reg.register(RespondTransferHeartsOver2NT())
    reg.register(RespondTransferSpadesOver2NT())
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
    # Gerber over 2NT now combined into RebidGerber* rules above
    reg.register(Rebid2NTCompleteTexas())

    # ── Opener rebids after 2NT opening (raises/declines) ──────────
    reg.register(Rebid2NTPassAfter3NT())
    reg.register(Rebid2NTAccept4NT())
    reg.register(Rebid2NTDecline4NT())

    # ── Responses to weak two (2D/2H/2S) ────────────────────────────
    reg.register(RespondGameRaiseWeakTwoMajor())
    reg.register(RespondGameRaiseWeakTwoMinor())
    reg.register(Respond3NTOverWeakTwo())
    reg.register(RespondNewSuitOverWeakTwo())
    reg.register(Respond2NTFeatureAsk())
    reg.register(RespondRaiseWeakTwo())
    reg.register(RespondPassOverWeakTwo())

    # ── Responses to 3-level preempt ─────────────────────────────────
    reg.register(RespondGameRaise3LevelMajor())
    reg.register(RespondGameRaise3LevelMinor())
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

    # ── Responder rebids after 1-of-a-suit (reresponse) ──────────────

    # After raise of major (1M->2M->rebid->?)
    reg.register(AcceptGameTry())
    reg.register(DeclineGameTry())
    reg.register(AcceptReraise())
    reg.register(DeclineReraise())
    reg.register(PassAfterGame())

    # After raise of minor (1m->2m->rebid->?)
    reg.register(PassAfterMinor3NT())
    reg.register(Accept2NTAfterMinorRaise())
    reg.register(Decline2NTAfterMinorRaise())
    reg.register(ThreeNTAfterMinorNewSuit())
    reg.register(Raise2ndSuitAfterMinorRaise())
    reg.register(ReturnToMinor())
    reg.register(AcceptMinorInvite())
    reg.register(DeclineMinorInvite())
    reg.register(PassAfterMinorGame())

    # After limit raise (1x->3x->rebid->?)
    reg.register(PassAfterAcceptedLimitRaise())
    reg.register(BlackwoodResponseAfterLimitRaise())

    # After Jacoby 2NT (1M->2NT->rebid->?)
    reg.register(Blackwood4NTAfterShortness())
    reg.register(Blackwood4NTAfterSource())
    reg.register(Blackwood4NTAfterMax())
    reg.register(Blackwood4NTAfter3NTMedium())
    reg.register(Blackwood4NTAfterJacoby4M())
    reg.register(Bid4MAfterShortness())
    reg.register(Bid4MAfterSource())
    reg.register(Bid4MAfterMax())
    reg.register(Bid4MAfter3NTMedium())
    reg.register(PassAfterJacoby4M())

    # After new suit at 1-level: 1NT rebid (1x->1y->1NT->?)
    reg.register(FourMAfter1NTRebid())
    reg.register(ThreeNTAfter1NTRebid())
    reg.register(JumpOwnMajorAfter1NT())
    reg.register(NewSuitAfter1NTForcing())
    reg.register(TwoNTAfter1NTRebid())
    reg.register(JumpRebidAfter1NT())
    reg.register(NewSuitWeakAfter1NT())
    reg.register(RebidOwnSuitAfter1NT())
    reg.register(PassAfter1NTRebid())

    # After new suit at 1-level: raise (1x->1y->2y->?)
    reg.register(FourMAfterRaise())
    reg.register(ThreeNTAfterRaise())
    reg.register(ThreeYInviteAfterRaise())
    reg.register(PassAfterRaise())

    # After new suit at 1-level: jump raise (1x->1y->3y->?)
    reg.register(Accept3yJumpRaise())
    reg.register(Accept3yJumpRaise3NT())
    reg.register(Decline3yJumpRaise())
    reg.register(PassAfterDoubleJumpRaise())

    # After new suit at 1-level: opener rebid own suit (1x->1y->2x->?)
    reg.register(NewSuitForcingAfterOwnSuit())
    reg.register(FourMAfterOwnSuitMajor())
    reg.register(ThreeNTAfterOwnSuit())
    reg.register(FourthSuitAfterOwnSuit())
    reg.register(JumpRebidOwnSuitAfterOwnSuit())
    reg.register(TwoNTAfterOwnSuit())
    reg.register(ThreeXInviteAfterOwnSuit())
    reg.register(RebidOwnSuitAfterOwnSuit())
    reg.register(PreferenceAfterOwnSuit())

    # After new suit at 1-level: jump rebid (1x->1y->3x->?)
    reg.register(FourMAfterJumpRebid())
    reg.register(ThreeNTAfterJumpRebidNoStoppers())
    reg.register(ThreeNTAfterJumpRebid())
    reg.register(PassAfterJumpRebid())

    # After new suit at 1-level: new suit non-reverse (1x->1y->2z->?)
    reg.register(NewSuitForcingAfterMinorRaise())
    reg.register(FourMAfterNewSuit())
    reg.register(ThreeNTAfterNewSuit())
    reg.register(FourthSuitForcing())
    reg.register(JumpRebidOwnSuitAfterNewSuit())
    reg.register(RaiseNewSuitInvite())
    reg.register(TwoNTAfterNewSuit())
    reg.register(PreferenceToOpenerFirst())
    reg.register(RebidOwnSuitAfterNewSuit())
    reg.register(PassAfterNewSuit())

    # After new suit at 1-level: new suit at 1-level (1x->1y->1z->?)
    reg.register(NewSuitAt1Level())
    reg.register(WeakRaiseNewSuit())
    reg.register(OneNTReresponse())

    # After new suit at 1-level: reverse (1x->1y->2z rev->?)
    reg.register(GFRaiseReverseSuit())
    reg.register(GFAfterReverse())
    reg.register(ThreeNTAfterReverse())
    reg.register(RaiseReverseSuit())
    reg.register(JumpInOwnSuitAfterReverse())
    reg.register(TwoNTAfterReverse())
    reg.register(RebidOwnSuitAfterReverse())
    reg.register(PreferenceAfterReverse())

    # After new suit at 1-level: jump shift (1x->1y->3z->?)
    reg.register(RaiseJumpShiftSuit())
    reg.register(SupportOpenerFirstAfterJS())
    reg.register(RebidOwnSuitAfterJS())
    reg.register(ThreeNTAfterJumpShift())

    # After new suit at 1-level: 2NT rebid (1x->1y->2NT->?)
    reg.register(FourMAfter2NTRebid())
    reg.register(ThreeNTAfter2NTRebid())
    reg.register(ThreeSuitAfter2NTRebid())
    reg.register(PassAfter2NTRebid())

    # After new suit at 1-level: 3NT rebid (1x->1y->3NT->?)
    reg.register(PassAfter3NTRebid())

    # After new suit at 1-level: double-jump rebid (1x->1y->4x->?)
    reg.register(PassAfterDoubleJumpRebid())

    # After 1NT response (1x->1NT->rebid->?)
    reg.register(PassAfterSuitRebid1NT())
    reg.register(RaiseNewSuit1NTResponse())
    reg.register(PreferenceTo1stSuit1NT())
    reg.register(PassAfterNewSuit1NT())
    reg.register(ThreeNTAfter2NTOver1NT())
    reg.register(PassAfter2NTOver1NT())
    reg.register(FourMAfterJumpRebidOver1NT())
    reg.register(ThreeNTAfterJumpRebidOver1NT())
    reg.register(PassAfterJumpRebidOver1NT())
    reg.register(PassAfter3NTOver1NT())
    reg.register(SupportJumpShiftOver1NT())
    reg.register(ReturnToOpenerSuitAfterJS1NT())
    reg.register(ThreeNTAfterJSOver1NT())

    # After reverse over 1NT response (1x->1NT->2z(rev)->?)
    reg.register(ThreeNTAfterReverseOver1NT())
    reg.register(RaiseReverseSuitOver1NT())
    reg.register(PreferenceAfterReverseOver1NT())
    reg.register(TwoNTAfterReverseOver1NT())

    # After game jump over 1NT response (1x->1NT->4x->?)
    reg.register(PassAfterGameJumpOver1NT())

    # After 2-over-1: raise (1x->2y->3y->?)
    reg.register(SlamTryMinorAfterRaise())
    reg.register(ThreeNTAfterRaise2Over1())
    reg.register(GameInMinorAfterRaise())
    reg.register(FourMAfterRaise2Over1())
    reg.register(PassAfterMinorRaise2Over1())

    # After 2-over-1: rebid own suit (1x->2y->2x->?)
    reg.register(FourMAfter2Over1OwnSuit())
    reg.register(ThreeNTAfter2Over1OwnSuit())
    reg.register(NewSuitAfter2Over1OwnSuit())
    reg.register(RaiseOpenerAfter2Over1())
    reg.register(RebidOwnSuitAfter2Over1())
    reg.register(TwoNTAfter2Over1())

    # After 2-over-1: new suit non-reverse (1x->2y->2z->?)
    reg.register(FourMAfter2Over1NewSuit())
    reg.register(ThreeNTAfter2Over1NewSuit())
    reg.register(FourthSuitAfter2Over1NS())
    reg.register(RaiseOpenerNewSuit2Over1())
    reg.register(PreferenceAfter2Over1NS())
    reg.register(RebidOwnAfter2Over1NS())
    reg.register(TwoNTAfter2Over1NS())

    # After 2-over-1: 2NT (1x->2y->2NT->?)
    reg.register(ThreeNTAfter2Over1_2NT())
    reg.register(ThreeSuitAfter2Over1_2NT())
    reg.register(PassAfter2Over1_2NT())

    # After 2-over-1: reverse (1x->2y->reverse->?)
    reg.register(ThreeNTAfterReverse2Over1())
    reg.register(RaiseReverseSuit2Over1())
    reg.register(RebidOwnAfterReverse2Over1())
    reg.register(PreferenceAfterReverse2Over1())
    reg.register(TwoNTAfterReverse2Over1())

    # After 2-over-1: 3NT (1x->2y->3NT->?)
    reg.register(PassAfter3NT2Over1())

    # After jump shift (1x->jump->rebid->?)
    reg.register(Blackwood4NTAfterJS())
    reg.register(ShowSecondSuitAfterJS())
    reg.register(FourMAfterJS())
    reg.register(ThreeNTAfterJSReresponse())

    # After 2NT over minor (1m->2NT->rebid->?)
    reg.register(ThreeNTAfter2NTMinorMajor())
    reg.register(ThreeNTAfter2NTMinorRebid())
    reg.register(PassAfter2NTMinor3NT())
    reg.register(AcceptQuantitative4NTMinor())
    reg.register(DeclineQuantitative4NTMinor())

    # After 3NT response
    reg.register(PassAfter3NTResponse())

    # ── Responder rebids after NT opening (reresponse) ──────────────

    # After Stayman denial over 1NT (1NT->2C->2D->?)
    reg.register(PassGarbageStayman())
    reg.register(InviteMajorAfterDenial())
    reg.register(Invite2NTAfterDenial())
    reg.register(GFMajorAfterDenial())
    reg.register(Game3NTAfterDenial())
    reg.register(SlamMinorAfterDenial())

    # After Stayman fit over 1NT (1NT->2C->2H/2S->?)
    reg.register(PassGarbageStaymanFit())
    reg.register(InviteRaiseStaymanFit())
    reg.register(GameRaiseStaymanFit())
    reg.register(Invite2NTStaymanNoFit())
    reg.register(Game3NTStaymanNoFit())

    # After Stayman denial over 2NT (2NT->3C->3D->?)
    reg.register(GFMajor2NTDenial())
    reg.register(Game3NT2NTDenial())
    reg.register(SlamMinor2NTDenial())
    reg.register(Quant4NT2NTDenial())

    # After Stayman fit over 2NT (2NT->3C->3H/3S->?)
    reg.register(GameRaise2NTStaymanFit())
    reg.register(Game3NT2NTNoFit())
    reg.register(Quant4NT2NTStaymanFit())

    # After normal transfer completion over 1NT (1NT->2D->2H->? or 1NT->2H->2S->?)
    reg.register(PassTransferSignoff())
    reg.register(Invite2NTAfterTransfer())
    reg.register(InviteRaiseTransfer())
    reg.register(InviteMajors55())
    reg.register(Game3NTAfterTransfer())
    reg.register(GameRaiseTransfer())
    reg.register(GFMajors55())

    # After super-accept over 1NT (1NT->2D->3H->? or 1NT->2H->3S->?)
    reg.register(PassSuperAccept())
    reg.register(Game3NTSuperAccept())
    reg.register(Game4MSuperAccept())
    reg.register(Quant4NTSuperAccept())

    # After transfer completion over 2NT (2NT->3D->3H->? or 2NT->3H->3S->?)
    reg.register(PassTransfer2NTSignoff())
    reg.register(Game3NTTransfer2NT())
    reg.register(Game4MTransfer2NT())
    reg.register(Quant4NTTransfer2NT())

    # After puppet completion over 1NT (1NT->2S->3C->?)
    reg.register(PassPuppetClubs())
    reg.register(CorrectPuppetDiamonds())

    # After puppet completion over 2NT (2NT->3S->4C->?)
    reg.register(PassPuppet2NTClubs())
    reg.register(CorrectPuppet2NTDiamonds())

    # After Gerber response over 1NT/2NT (xNT->4C->response->?)
    reg.register(KingAskAfterGerber())
    reg.register(SignoffAfterGerber())
    reg.register(PassAfterGerber())

    # After Texas transfer completion (xNT->4D/4H->4H/4S->Pass)
    reg.register(PassAfterTexas())

    # Catch-all pass for NT auctions
    reg.register(PassAfterNTReresponse())

    return reg
