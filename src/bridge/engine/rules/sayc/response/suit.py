"""Responses to 1-of-a-suit opening — SAYC.

All response rules for when partner opens 1C, 1D, 1H, or 1S (uncontested).
Organized into shared rules (apply over any 1-suit opening), major-specific
rules, and minor-specific rules.
"""

from __future__ import annotations

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.evaluate import support_points
from bridge.model.bid import Bid
from bridge.model.card import Suit

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
    assert bid.suit is not None
    return bid.suit


def _opened_1_suit(ctx: BiddingContext) -> bool:
    """Whether partner opened 1 of any suit (not NT)."""
    bid = _opening_bid(ctx)
    return bid.level == 1 and bid.suit is not None and bid.suit != Suit.NOTRUMP


def _opened_1_major(ctx: BiddingContext) -> bool:
    """Whether partner opened 1H or 1S."""
    bid = _opening_bid(ctx)
    return bid.level == 1 and bid.suit is not None and bid.suit.is_major


def _opened_1_minor(ctx: BiddingContext) -> bool:
    """Whether partner opened 1C or 1D."""
    bid = _opening_bid(ctx)
    return bid.level == 1 and bid.suit is not None and bid.suit.is_minor


def _has_4_card_major(ctx: BiddingContext) -> bool:
    """Whether responder has a 4+ card major."""
    hand = ctx.hand
    return hand.suit_length(Suit.SPADES) >= 4 or hand.suit_length(Suit.HEARTS) >= 4


def _adequate_minor_support(ctx: BiddingContext) -> bool:
    """Whether responder has adequate support for opener's minor.

    SAYC: 4+ for diamonds, 5+ for clubs.
    """
    suit = _opener_suit(ctx)
    length = ctx.hand.suit_length(suit)
    if suit == Suit.DIAMONDS:
        return length >= 4
    return length >= 5  # clubs


def _find_new_suit_1_level(ctx: BiddingContext) -> Suit | None:
    """Find cheapest 4+ card suit biddable at the 1-level above opener's bid.

    Searches up the line from just above opener's suit.
    """
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

    Over 1C: nothing (all suits are higher → 1-level).
    Over 1D: 2C only.
    Over 1H: 2C, 2D.
    Over 1S: 2C, 2D, 2H.
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

    @property
    def name(self) -> str:
        return "response.jump_shift"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 380

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_suit(ctx):
            return False
        if ctx.hcp < 19:
            return False
        return _find_jump_shift_suit(ctx) is not None

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _find_jump_shift_suit(ctx)
        assert suit is not None
        level = _jump_level(_opener_suit(ctx), suit)
        return RuleResult(
            bid=Bid.suit_bid(level, suit),
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

    @property
    def name(self) -> str:
        return "response.new_suit_1_level"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 260

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_suit(ctx):
            return False
        if ctx.hcp < 6:
            return False
        return _find_new_suit_1_level(ctx) is not None

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _find_new_suit_1_level(ctx)
        assert suit is not None
        return RuleResult(
            bid=Bid.suit_bid(1, suit),
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

    @property
    def name(self) -> str:
        return "response.2_over_1"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 240

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_suit(ctx):
            return False
        if ctx.hcp < 10 or ctx.hcp >= 19:
            return False
        return _find_2_over_1_suit(ctx) is not None

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _find_2_over_1_suit(ctx)
        assert suit is not None
        return RuleResult(
            bid=Bid.suit_bid(2, suit),
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

    def applies(self, ctx: BiddingContext) -> bool:
        return _opened_1_suit(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.make_pass(),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        suit = _opener_suit(ctx)
        if ctx.hand.suit_length(suit) < 4:
            return False
        return support_points(ctx.hand, suit) >= 13

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(2, Suit.NOTRUMP),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        suit = _opener_suit(ctx)
        if ctx.hand.suit_length(suit) < 5:
            return False
        if ctx.hcp >= 10:
            return False
        # Must have singleton or void in a side suit
        for s in (Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS):
            if s != suit and ctx.hand.suit_length(s) <= 1:
                return True
        return False

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(4, _opener_suit(ctx)),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        suit = _opener_suit(ctx)
        if ctx.hand.suit_length(suit) != 2:
            return False
        return 15 <= ctx.hcp <= 17 and ctx.is_balanced

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=("15-17 HCP, balanced, 2-card support — SAYC 3NT over major"),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        suit = _opener_suit(ctx)
        if ctx.hand.suit_length(suit) < 3:
            return False
        return 10 <= support_points(ctx.hand, suit) <= 12

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(3, _opener_suit(ctx)),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        suit = _opener_suit(ctx)
        if ctx.hand.suit_length(suit) < 3:
            return False
        return 6 <= support_points(ctx.hand, suit) <= 10

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(2, _opener_suit(ctx)),
            rule_name=self.name,
            explanation=("3+ card support, 6-10 support points — SAYC single raise"),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_major(ctx):
            return False
        if not (6 <= ctx.hcp <= 10):
            return False
        return ctx.hand.suit_length(_opener_suit(ctx)) < 3

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=("6-10 HCP, no 3+ support — SAYC 1NT response, non-forcing"),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_minor(ctx):
            return False
        if not (16 <= ctx.hcp <= 18):
            return False
        if not ctx.is_balanced:
            return False
        return not _has_4_card_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=("16-18 HCP, balanced, no 4-card major — SAYC 3NT over minor"),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_minor(ctx):
            return False
        if not (13 <= ctx.hcp <= 15):
            return False
        if not ctx.is_balanced:
            return False
        return not _has_4_card_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(2, Suit.NOTRUMP),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_minor(ctx):
            return False
        if not (10 <= ctx.hcp <= 12):
            return False
        if not _adequate_minor_support(ctx):
            return False
        return not _has_4_card_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(3, _opener_suit(ctx)),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_minor(ctx):
            return False
        if not (6 <= ctx.hcp <= 10):
            return False
        if not _adequate_minor_support(ctx):
            return False
        return not _has_4_card_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(2, _opener_suit(ctx)),
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

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1_minor(ctx):
            return False
        if not (6 <= ctx.hcp <= 10):
            return False
        return not _has_4_card_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "6-10 HCP, no 4-card major — SAYC 1NT over minor, non-forcing"
            ),
        )
