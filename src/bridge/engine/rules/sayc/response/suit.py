"""Responses to 1-of-a-suit opening — SAYC.

All response rules for when partner opens 1C, 1D, 1H, or 1S (uncontested).
Organized into shared rules (apply over any 1-suit opening), major-specific
rules, and minor-specific rules.
"""

from __future__ import annotations

from bridge.engine.condition import (
    All,
    Balanced,
    Computed,
    Condition,
    HasSuitFit,
    HcpRange,
    Not,
    SupportPtsRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, Bid, SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Suit

# ── Helpers ─────────────────────────────────────────────────────────


def _opening_bid(ctx: BiddingContext) -> Bid:
    """Return partner's opening bid.

    Only valid in the RESPONSE phase — the phase detector guarantees
    an opening bid exists before any response rule runs.
    """
    assert ctx.opening_bid is not None, "No opening bid — wrong bidding phase"
    return ctx.opening_bid[1]


def _opener_suit(ctx: BiddingContext) -> Suit:
    """Return the suit (or NOTRUMP) partner opened.

    An opening bid is always a suit bid (never pass/double), so suit
    is guaranteed non-None.
    """
    bid = _opening_bid(ctx)
    assert is_suit_bid(bid)
    return bid.suit


# ── Conditions ─────────────────────────────────────────────────────


@condition("partner opened 1 of a suit")
def _partner_opened_1_suit(ctx: BiddingContext) -> bool:
    bid = _opening_bid(ctx)
    return is_suit_bid(bid) and bid.level == 1 and bid.suit != Suit.NOTRUMP


@condition("partner opened 1 of a major")
def _partner_opened_1_major(ctx: BiddingContext) -> bool:
    bid = _opening_bid(ctx)
    return is_suit_bid(bid) and bid.level == 1 and bid.suit.is_major


@condition("partner opened 1 of a minor")
def _partner_opened_1_minor(ctx: BiddingContext) -> bool:
    bid = _opening_bid(ctx)
    return is_suit_bid(bid) and bid.level == 1 and bid.suit.is_minor


@condition("has 4+ card major")
def has_4_card_major(ctx: BiddingContext) -> bool:
    return ctx.hand.num_spades >= 4 or ctx.hand.num_hearts >= 4


@condition("adequate minor support")
def adequate_minor_support(ctx: BiddingContext) -> bool:
    """SAYC: 4+ for diamonds, 5+ for clubs."""
    suit = _opener_suit(ctx)
    length = ctx.hand.suit_length(suit)
    return length >= 4 if suit == Suit.DIAMONDS else length >= 5


@condition("has singleton or void in side suit")
def _has_side_shortness(ctx: BiddingContext) -> bool:
    suit = _opener_suit(ctx)
    return any(s != suit and ctx.hand.suit_length(s) <= 1 for s in SUITS_SHDC)


def _find_new_suit_1_level(ctx: BiddingContext) -> Suit | None:
    """Find cheapest 4+ card suit biddable at the 1-level above opener's bid."""
    opener = _opener_suit(ctx)
    hand = ctx.hand
    for suit in (Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit > opener and hand.suit_length(suit) >= 4:
            return suit
    return None


def _find_2_over_1_suit(ctx: BiddingContext) -> Suit | None:
    """Find the best suit for a 2-over-1 response.

    A 2-over-1 bid is a new suit that ranks LOWER than opener's suit,
    so it must be bid at the 2-level.  Bid the longest qualifying suit;
    with ties, bid the cheapest (up the line).
    """
    opener = _opener_suit(ctx)
    hand = ctx.hand
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS):
        if suit < opener:
            length = hand.suit_length(suit)
            if length >= 4 and length > best_len:
                best = suit
                best_len = length
    return best


def _find_jump_shift_suit(ctx: BiddingContext) -> Suit | None:
    """Find the best suit for a jump shift response.

    Bid the longest new suit; with ties, bid the higher-ranking.
    Jump shifts can be in any suit (higher or lower than opener's).
    """
    opener = _opener_suit(ctx)
    hand = ctx.hand
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == opener:
            continue
        length = hand.suit_length(suit)
        if length >= 4 and (
            length > best_len
            or (length == best_len and best is not None and suit > best)
        ):
            best = suit
            best_len = length
    return best


def _jump_level(opener_suit: Suit, new_suit: Suit) -> int:
    """Calculate the level for a jump shift (one level above a simple bid)."""
    if new_suit > opener_suit:
        return 2  # e.g., 1H→2S (jump over simple 1S)
    return 3  # e.g., 1H→3C, 1S→3H (jump over 2-level)


# ── Shared Rules ────────────────────────────────────────────────────


class RespondJumpShift(Rule):
    """Jump shift response: 19+ HCP, 4+ card new suit.

    SAYC: "19+ points, 4+ cards in new suit; slam invitational."
    Applies over both major and minor openings.
    """

    def __init__(self) -> None:
        self._suit = Computed(_find_jump_shift_suit, "4+ card new suit for jump shift")

    @property
    def name(self) -> str:
        return "response.jump_shift"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 380

    @property
    def conditions(self) -> Condition:
        return All(_partner_opened_1_suit, HcpRange(min_hcp=19), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        level = _jump_level(_opener_suit(ctx), suit)
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(
                f"19+ HCP, {suit.letter} suit — SAYC jump shift, slam invitational"
            ),
            forcing=True,
        )


class RespondNewSuit1Level(Rule):
    """Bid a new suit at the 1-level: 4+ cards, 6+ HCP.

    SAYC: "4+ cards, 6+ points; forcing one round."
    Over 1C: can bid 1D, 1H, or 1S.
    Over 1D: can bid 1H or 1S.
    Over 1H: can bid 1S.
    Over 1S: no higher suit at 1-level.
    With multiple suits, bid up the line (cheapest first).
    """

    def __init__(self) -> None:
        self._suit = Computed(_find_new_suit_1_level, "4+ card suit at 1-level")

    @property
    def name(self) -> str:
        return "response.new_suit_1_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 260

    @property
    def conditions(self) -> Condition:
        return All(_partner_opened_1_suit, HcpRange(min_hcp=6), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        return RuleResult(
            bid=SuitBid(1, suit),
            rule_name=self.name,
            explanation=(
                f"4+ card {suit.letter}, 6+ HCP — SAYC new suit at 1-level, forcing"
            ),
            forcing=True,
        )


class Respond2Over1(Rule):
    """Bid a new suit at the 2-level: 4+ cards, 10+ HCP.

    SAYC: "4+ cards, 10+ points; forcing one round."
    Applies over both major and minor openings.
    """

    def __init__(self) -> None:
        self._suit = Computed(_find_2_over_1_suit, "4+ card suit for 2-over-1")

    @property
    def name(self) -> str:
        return "response.2_over_1"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 240

    @property
    def conditions(self) -> Condition:
        return All(_partner_opened_1_suit, HcpRange(min_hcp=10, max_hcp=18), self._suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._suit.value
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=(
                f"10+ HCP, 4+ card {suit.letter} — SAYC 2-over-1, forcing one round"
            ),
            forcing=True,
        )


class RespondPass(Rule):
    """Pass with fewer than 6 HCP.

    Fallback for all 1-suit openings.
    """

    @property
    def name(self) -> str:
        return "response.pass"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 50

    @property
    def conditions(self) -> Condition:
        return All(_partner_opened_1_suit, HcpRange(max_hcp=5))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Fewer than 6 HCP — pass",
        )


# ── Major-Specific Rules ───────────────────────────────────────────


class RespondJacoby2NT(Rule):
    """Jacoby 2NT: 4+ card support, 13+ support points.

    SAYC: "4+ card support, 13+ dummy points; game forcing."
    """

    @property
    def name(self) -> str:
        return "response.jacoby_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 340

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HasSuitFit(_opener_suit, min_len=4),
            SupportPtsRange(_opener_suit, min_pts=13),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "4+ card support, 13+ support points — SAYC Jacoby 2NT, game forcing"
            ),
            alerts=("Jacoby 2NT — game forcing raise",),
            forcing=True,
        )


class RespondGameRaiseMajor(Rule):
    """Preemptive game raise: 5+ support, <10 HCP, singleton/void.

    SAYC: "5+ card support, singleton or void, fewer than 10 HCP."
    """

    @property
    def name(self) -> str:
        return "response.game_raise_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 320

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HasSuitFit(_opener_suit, min_len=5),
            HcpRange(max_hcp=9),
            _has_side_shortness,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, _opener_suit(ctx)),
            rule_name=self.name,
            explanation=(
                "5+ card support, singleton/void, <10 HCP — SAYC preemptive game raise"
            ),
        )


class Respond3NTOverMajor(Rule):
    """3NT over major: 15-17 HCP, balanced, exactly 2-card support.

    SAYC: "15-17 HCP, balanced, exactly 2-card support; to play."
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 300

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HasSuitFit(_opener_suit, min_len=2, max_len=2),
            HcpRange(15, 17),
            Balanced(strict=True),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15-17 HCP, balanced, 2-card support — SAYC 3NT over major",
        )


class RespondLimitRaiseMajor(Rule):
    """Limit raise: 3+ support, 10-12 support points.

    SAYC: "3+ card support, 10-12 dummy points; invitational."
    """

    @property
    def name(self) -> str:
        return "response.limit_raise_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 280

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HasSuitFit(_opener_suit, min_len=3),
            SupportPtsRange(_opener_suit, min_pts=10, max_pts=12),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, _opener_suit(ctx)),
            rule_name=self.name,
            explanation=(
                "3+ card support, 10-12 support points — SAYC limit raise, invitational"
            ),
        )


class RespondSingleRaiseMajor(Rule):
    """Single raise: 3+ support, 6-10 support points.

    SAYC: "3+ card support, 6-10 dummy points."
    """

    @property
    def name(self) -> str:
        return "response.single_raise_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 220

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HasSuitFit(_opener_suit, min_len=3),
            SupportPtsRange(_opener_suit, min_pts=6, max_pts=10),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, _opener_suit(ctx)),
            rule_name=self.name,
            explanation="3+ card support, 6-10 support points — SAYC single raise",
        )


class Respond1NTOverMajor(Rule):
    """1NT response: 6-10 HCP, denies 3+ support, denies 4S over 1H.

    SAYC: "6-10 HCP; denies 3-card support; denies 4 spades over 1H;
    non-forcing."
    """

    @property
    def name(self) -> str:
        return "response.1nt_over_major"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 200

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_major,
            HcpRange(6, 10),
            HasSuitFit(_opener_suit, min_len=0, max_len=2),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="6-10 HCP, no 3+ support — SAYC 1NT response, non-forcing",
        )


# ── Minor-Specific Rules ───────────────────────────────────────────


class Respond3NTOverMinor(Rule):
    """3NT over minor: 16-18 HCP, balanced, no 4-card major.

    SAYC: "16-18 HCP, balanced, denies 4-card major; to play."
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 310

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_minor,
            HcpRange(16, 18),
            Balanced(strict=True),
            Not(has_4_card_major),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16-18 HCP, balanced, no 4-card major — SAYC 3NT over minor",
        )


class Respond2NTOverMinor(Rule):
    """2NT over minor: 13-15 HCP, balanced, no 4-card major.

    SAYC: "13-15 HCP, balanced, denies 4-card major; game forcing."
    """

    @property
    def name(self) -> str:
        return "response.2nt_over_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 290

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_minor,
            HcpRange(13, 15),
            Balanced(strict=True),
            Not(has_4_card_major),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "13-15 HCP, balanced, no 4-card major"
                " — SAYC 2NT over minor, game forcing"
            ),
            forcing=True,
        )


class RespondLimitRaiseMinor(Rule):
    """Limit raise of minor: 10-12 HCP, adequate support.

    SAYC: "Adequate trump support, 10-12 points; invitational."
    Uses HCP only (no support points for minor raises).
    """

    @property
    def name(self) -> str:
        return "response.limit_raise_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 270

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_minor,
            HcpRange(10, 12),
            adequate_minor_support,
            Not(has_4_card_major),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, _opener_suit(ctx)),
            rule_name=self.name,
            explanation=(
                "10-12 HCP, adequate support — SAYC limit raise of minor, invitational"
            ),
        )


class RespondSingleRaiseMinor(Rule):
    """Single raise of minor: 6-10 HCP, adequate support, no 4-card major.

    SAYC: "Adequate trump support, 6-10 points."
    Uses HCP only (no support points for minor raises).
    """

    @property
    def name(self) -> str:
        return "response.single_raise_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 230

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_minor,
            HcpRange(6, 10),
            adequate_minor_support,
            Not(has_4_card_major),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, _opener_suit(ctx)),
            rule_name=self.name,
            explanation=(
                "6-10 HCP, adequate support, no 4-card major"
                " — SAYC single raise of minor"
            ),
        )


class Respond1NTOverMinor(Rule):
    """1NT over minor: 6-10 HCP, no 4-card major.

    SAYC: "6-10 HCP, no 4-card major; non-forcing."
    """

    @property
    def name(self) -> str:
        return "response.1nt_over_minor"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 210

    @property
    def conditions(self) -> Condition:
        return All(
            _partner_opened_1_minor,
            HcpRange(6, 10),
            Not(has_4_card_major),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "6-10 HCP, no 4-card major — SAYC 1NT over minor, non-forcing"
            ),
        )
