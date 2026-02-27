"""Opener's rebid rules — SAYC.

After opening 1 of a suit and hearing partner's response (uncontested),
opener rebids based on hand strength and shape.  Rules are organized by
the type of response partner made:

- Single raise (1M→2M, 1m→2m)
- Limit raise (1M→3M, 1m→3m)
- 1NT response
- New suit at the 1-level (e.g., 1D→1H)
- 2-over-1 new suit (e.g., 1H→2C)
- Jacoby 2NT (1M→2NT)
- Jump shift (e.g., 1H→2S, 1D→2H)
- 3NT response
- 4M preemptive raise
- 2NT over minor (1m→2NT)

All rules belong to Category.REBID_OPENER.
"""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit, suit_hcp
from bridge.engine.condition import (
    All,
    Any,
    Balanced,
    BergenPtsRange,
    Computed,
    Condition,
    HasSuitFit,
    HcpRange,
    Not,
    TotalPtsRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import Suit

# ── Helpers ─────────────────────────────────────────────────────────


def _my_opening_bid(ctx: BiddingContext) -> SuitBid:
    """Return opener's first bid (always a suit bid in this module)."""
    bid = ctx.my_bids[0]
    assert is_suit_bid(bid)
    return bid


def _my_opening_suit(ctx: BiddingContext) -> Suit:
    """Return the suit opener bid (never NOTRUMP for 1-suit openings)."""
    bid = _my_opening_bid(ctx)
    assert not bid.is_notrump
    return bid.suit


def _partner_response(ctx: BiddingContext) -> SuitBid:
    """Return partner's response bid (always a suit bid in uncontested auctions)."""
    resp = ctx.partner_last_bid
    assert resp is not None and is_suit_bid(resp)
    return resp


@condition("I opened 1 of a suit")
def _i_opened_1_suit(ctx: BiddingContext) -> bool:
    """Guard: opener's first bid was 1 of a suit (not NT)."""
    bid = _my_opening_bid(ctx)
    return bid.level == 1 and not bid.is_notrump


# ── Response classifiers ────────────────────────────────────────────


@condition("partner single-raised")
def _partner_single_raised(ctx: BiddingContext) -> bool:
    """Partner made a single raise (1M→2M or 1m→2m)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 1


@condition("partner limit-raised")
def _partner_limit_raised(ctx: BiddingContext) -> bool:
    """Partner made a limit raise (1M→3M or 1m→3m)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 2


@condition("partner bid 1NT")
def _partner_bid_1nt(ctx: BiddingContext) -> bool:
    """Partner responded 1NT."""
    resp = _partner_response(ctx)
    return resp.is_notrump and resp.level == 1


def _partner_bid_new_suit(ctx: BiddingContext) -> bool:
    """Partner bid a new suit (not a raise, not NT)."""
    resp = _partner_response(ctx)
    return not resp.is_notrump and resp.suit != _my_opening_suit(ctx)


@condition("partner bid new suit at 1-level")
def _partner_bid_new_suit_1_level(ctx: BiddingContext) -> bool:
    """Partner bid a new suit at the 1-level."""
    return _partner_bid_new_suit(ctx) and _partner_response(ctx).level == 1


@condition("partner bid 2-over-1")
def _partner_bid_2_over_1(ctx: BiddingContext) -> bool:
    """Partner bid a new suit at the 2-level (2-over-1).

    Excludes jump shifts (which are a level higher than necessary).
    """
    if not _partner_bid_new_suit(ctx):
        return False
    resp = _partner_response(ctx)
    if resp.level != 2:
        return False
    # Exclude jump shifts: if responder could have bid this suit at 1-level,
    # then bidding at 2-level is a jump shift, not a 2-over-1.
    return not _partner_jump_shifted(ctx)


@condition("partner bid 3NT")
def _partner_bid_3nt(ctx: BiddingContext) -> bool:
    """Partner responded 3NT."""
    resp = _partner_response(ctx)
    return resp.is_notrump and resp.level == 3


@condition("partner bid game raise")
def _partner_bid_game_raise(ctx: BiddingContext) -> bool:
    """Partner made a preemptive game raise (4M)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.suit == opening.suit and resp.level == 4 and opening.suit.is_major


@condition("partner bid Jacoby 2NT")
def _partner_bid_jacoby_2nt(ctx: BiddingContext) -> bool:
    """Partner responded 2NT to our 1M opening (Jacoby 2NT)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.is_notrump and resp.level == 2 and opening.suit.is_major


@condition("partner bid 2NT over minor")
def _partner_bid_2nt_over_minor(ctx: BiddingContext) -> bool:
    """Partner responded 2NT to our 1m opening."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.is_notrump and resp.level == 2 and opening.suit.is_minor


@condition("partner jump-shifted")
def _partner_jump_shifted(ctx: BiddingContext) -> bool:
    """Partner made a jump shift -- new suit one level higher than necessary.

    A jump shift means responder bid a new suit at a higher level than the
    cheapest possible. For example:
    - After 1C: 2D is a jump shift (could bid 1D), 2H (could bid 1H), etc.
    - After 1D: 2H is a jump shift (could bid 1H), but 2C is NOT (cheapest).
    - After 1H: 2S is a jump shift (could bid 1S), 3C/3D are jump shifts.
    - After 1S: 3C/3D/3H are jump shifts.
    """
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    if resp.is_notrump:
        return False
    if resp.suit == opening.suit:
        return False  # raise, not a new suit
    # Compute cheapest legal level for responder's suit above the opening bid
    cheapest = cheapest_bid_in_suit(resp.suit, opening)
    return resp.level > cheapest.level


# ── Suit-finding helpers ────────────────────────────────────────────


@condition("6+ card opening suit")
def _has_rebiddable_suit(ctx: BiddingContext) -> bool:
    """Whether opener has 6+ cards in their opening suit."""
    return ctx.hand.suit_length(_my_opening_suit(ctx)) >= 6


def _find_lower_new_suit(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card suit biddable at the 2-level below the opening suit.

    Used for non-reverse rebids over 1NT.  Returns the longest qualifying
    suit; cheapest breaks ties.
    """
    opening_suit = _my_opening_suit(ctx)
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit >= opening_suit:
            break
        length = ctx.hand.suit_length(suit)
        if length >= 4 and length > best_len:
            best = suit
            best_len = length
    return best


def _find_new_suit_for_rebid(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card second suit for a new-suit rebid.

    Returns the longest qualifying suit; cheapest bid breaks ties.
    Excludes the opening suit and responder's suit.
    """
    opening_suit = _my_opening_suit(ctx)
    resp = _partner_response(ctx)
    resp_suit = resp.suit
    best: Suit | None = None
    best_len = 0
    best_bid: SuitBid | None = None
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit in (opening_suit, resp_suit):
            continue
        length = ctx.hand.suit_length(suit)
        if length < 4:
            continue
        candidate = cheapest_bid_in_suit(suit, resp)
        is_better = length > best_len or (
            length == best_len and best_bid is not None and candidate < best_bid
        )
        if is_better:
            best = suit
            best_len = length
            best_bid = candidate
    return best


def _find_nonreverse_new_suit(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card new suit that is NOT a reverse.

    A non-reverse is a new suit that can be bid without forcing responder
    to the 3-level to return to opener's first suit.  This means:
    - At the 1-level (suit ranks higher than responder's suit), or
    - At the 2-level but ranking lower than the opening suit.
    """
    opening_suit = _my_opening_suit(ctx)
    resp = _partner_response(ctx)
    resp_suit = resp.suit
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit in (opening_suit, resp_suit):
            continue
        length = ctx.hand.suit_length(suit)
        if length < 4:
            continue
        # A reverse is a new suit ranking above the opening suit at the
        # 2-level, forcing responder to the 3-level to preference back.
        is_reverse = suit > opening_suit and suit < resp_suit
        if not is_reverse and length > best_len:
            best = suit
            best_len = length
    return best


def _find_reverse_suit(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card suit for a reverse bid.

    A reverse is a new suit ranking higher than the opening suit, bid at
    the 2-level.  The opening suit must be strictly longer than the new suit.

    Only suits that actually require a 2-level bid qualify.  If the suit
    ranks above responder's suit, it can be bid at the 1-level and is NOT
    a reverse (e.g. 1D-1H-1S is not a reverse).
    """
    opening_suit = _my_opening_suit(ctx)
    opening_len = ctx.hand.suit_length(opening_suit)
    resp_suit = _partner_response(ctx).suit
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit <= opening_suit:
            continue
        # Suit ranks above responder's -> biddable at 1-level, not a reverse
        if suit > resp_suit:
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 4 and opening_len > length and length > best_len:
            best = suit
            best_len = length
    return best


def _find_shortness_suit(ctx: BiddingContext) -> Suit | None:
    """Find a side suit with 0 or 1 cards (singleton or void).

    Returns the shortest side suit; with ties, returns the cheapest.
    Excludes the trump (opening) suit.
    """
    trump = _my_opening_suit(ctx)
    best: Suit | None = None
    best_len = 2  # must be < 2 to qualify
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == trump:
            continue
        length = ctx.hand.suit_length(suit)
        if length < best_len:
            best = suit
            best_len = length
    return best


def _find_5_card_side_suit(ctx: BiddingContext) -> Suit | None:
    """Find a side suit with 5+ cards (source of tricks).

    Returns the longest qualifying suit; cheapest breaks ties.
    Excludes the trump (opening) suit.
    """
    trump = _my_opening_suit(ctx)
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == trump:
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 5 and length > best_len:
            best = suit
            best_len = length
    return best


def _find_help_suit(ctx: BiddingContext) -> Suit | None:
    """Find the weakest 3+ card side suit for a help suit game try.

    A help suit is where opener needs partner's cards to cover losers.
    Must have at most 4 HCP (e.g. Kxx, Axx, Jxxx — not KQx or AKx).
    Picks the weakest suit (fewest HCP); cheapest bid breaks ties.
    Must be biddable below 3M.  Excludes the trump suit.
    Returns None if no side suit qualifies (all are well-held).
    """
    trump = _my_opening_suit(ctx)
    resp = _partner_response(ctx)
    best: Suit | None = None
    best_hcp = 99
    best_bid: SuitBid | None = None
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == trump:
            continue
        if ctx.hand.suit_length(suit) < 3:
            continue
        suit_pts = suit_hcp(ctx, suit)
        if suit_pts > 4:
            continue
        candidate = cheapest_bid_in_suit(suit, resp)
        if candidate >= SuitBid(3, trump):
            continue
        is_better = suit_pts < best_hcp or (
            suit_pts == best_hcp and best_bid is not None and candidate < best_bid
        )
        if is_better:
            best = suit
            best_hcp = suit_pts
            best_bid = candidate
    return best


def _jump_bid_in_suit(suit: Suit, above: SuitBid) -> SuitBid:
    """Return a jump bid (one level above cheapest) in the given suit."""
    cheapest = cheapest_bid_in_suit(suit, above)
    return SuitBid(cheapest.level + 1, suit)


# ── Additional condition helpers ───────────────────────────────────


@condition("opening suit is major")
def _opening_suit_is_major(ctx: BiddingContext) -> bool:
    return _my_opening_suit(ctx).is_major


@condition("opening suit is minor")
def _opening_suit_is_minor(ctx: BiddingContext) -> bool:
    return _my_opening_suit(ctx).is_minor


@condition("4+ card major")
def _has_4_card_major(ctx: BiddingContext) -> bool:
    return ctx.hand.num_hearts >= 4 or ctx.hand.num_spades >= 4


@condition("no 4+ card major")
def _no_4_card_major(ctx: BiddingContext) -> bool:
    return ctx.hand.num_hearts < 4 and ctx.hand.num_spades < 4


@condition("shortness (singleton or void)")
def _has_shortness(ctx: BiddingContext) -> bool:
    return _find_shortness_suit(ctx) is not None


@condition("5+ card side suit")
def _has_side_suit(ctx: BiddingContext) -> bool:
    return _find_5_card_side_suit(ctx) is not None


def _responder_suit(ctx: BiddingContext) -> Suit:
    """Responder's suit (for HasSuitFit/SuitLength)."""
    return _partner_response(ctx).suit


# ── Rules — After Single Raise of Major ─────────────────────────────


class RebidGameAfterRaiseMajor(Rule):
    """Bid game after partner single-raises your major — 19+ Bergen pts.

    e.g. 1S→2S→4S

    SAYC: "19+ points opposite a single raise; enough for game."
    """

    @property
    def name(self) -> str:
        return "rebid.game_after_raise_major"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 300

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_major,
            BergenPtsRange(_my_opening_suit, min_pts=19),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"19+ Bergen pts, game after single raise — SAYC 4{suit.letter}"
            ),
        )


class RebidInviteAfterRaiseMajor(Rule):
    """Invite game after partner single-raises your major — 16-18 Bergen pts.

    e.g. 1H→2H→3H

    SAYC: "16-18 points; invitational. Raise to 3."
    """

    @property
    def name(self) -> str:
        return "rebid.invite_after_raise_major"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 220

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_major,
            BergenPtsRange(_my_opening_suit, min_pts=16, max_pts=18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(f"16-18 Bergen pts, invitational raise — SAYC 3{suit.letter}"),
        )


class RebidPassAfterRaise(Rule):
    """Pass after partner single-raises — minimum Bergen pts.

    e.g. 1S→2S→Pass, 1D→2D→Pass

    Shared between major and minor raises.
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 60

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            BergenPtsRange(_my_opening_suit, max_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Minimum Bergen pts, content with partscore — pass",
        )


# ── Rules — After Limit Raise of Major ──────────────────────────────


class RebidAcceptLimitRaiseMajor(Rule):
    """Accept limit raise — 15+ Bergen pts, bid game.

    e.g. 1H→3H→4H

    SAYC: "Accept the invitation; bid game."
    """

    @property
    def name(self) -> str:
        return "rebid.accept_limit_raise_major"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 310

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_limit_raised,
            _opening_suit_is_major,
            BergenPtsRange(_my_opening_suit, min_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(f"15+ Bergen pts, accept limit raise — SAYC 4{suit.letter}"),
        )


class RebidDeclineLimitRaise(Rule):
    """Decline limit raise — <=14 Bergen pts.

    e.g. 1S→3S→Pass, 1D→3D→Pass

    Shared between major and minor.
    """

    @property
    def name(self) -> str:
        return "rebid.decline_limit_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 70

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_limit_raised,
            BergenPtsRange(_my_opening_suit, max_pts=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="<=14 Bergen pts, decline limit raise — pass",
        )


# ── Rules — After Raise of Minor ────────────────────────────────────


class Rebid3NTAfterRaiseMinor(Rule):
    """Bid 3NT after minor raise — balanced with sufficient HCP.

    e.g. 1D→2D→3NT, 1C→3C→3NT

    After a single raise: 18-19 HCP balanced.
    After a limit raise: 12+ HCP balanced.
    """

    @property
    def name(self) -> str:
        return "rebid.3nt_after_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 320

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _opening_suit_is_minor,
            Balanced(),
            Any(
                All(_partner_single_raised, HcpRange(18, 19)),
                All(_partner_limit_raised, HcpRange(min_hcp=12)),
            ),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Balanced, sufficient HCP after minor raise — SAYC 3NT",
        )


class Rebid2NTAfterRaiseMinor(Rule):
    """Bid 2NT after single raise of minor — 12-14 HCP balanced.

    e.g. 1D→2D→2NT

    Shows a balanced minimum over the single raise.
    """

    @property
    def name(self) -> str:
        return "rebid.2nt_after_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 210

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_minor,
            Balanced(),
            HcpRange(12, 14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12-14 HCP balanced after minor raise — SAYC 2NT",
        )


class RebidNewSuitAfterRaiseMinor(Rule):
    """Bid a new suit after single raise of minor — 15+ Bergen pts, unbalanced.

    e.g. 1D→2D→2H
    """

    @property
    def name(self) -> str:
        return "rebid.new_suit_after_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_for_rebid, "4+ card new suit")

    @property
    def priority(self) -> int:
        return 170

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_minor,
            BergenPtsRange(_my_opening_suit, min_pts=15),
            self._new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"15+ Bergen pts, new suit after minor raise — {bid}",
        )


class RebidGameAfterSingleRaiseMinor(Rule):
    """Bid 5 of minor after single raise — 19+ Bergen pts, unbalanced.

    e.g. 1D→2D→5D

    With game-level Bergen pts but no balanced shape for 3NT,
    bid game directly in the minor.
    """

    @property
    def name(self) -> str:
        return "rebid.game_after_single_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 175

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_minor,
            Not(Balanced(), label="balanced/semi-balanced"),
            BergenPtsRange(_my_opening_suit, min_pts=19),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"19+ Bergen pts, unbalanced — game in {suit.letter}",
        )


class RebidInviteAfterRaiseMinor(Rule):
    """Invite game after single raise of minor — 16-18 Bergen pts, unbalanced.

    e.g. 1D→2D→3D

    Mirrors RebidInviteAfterRaiseMajor but for minors. Covers hands
    with extras but no 4+ side suit to show (those use
    RebidNewSuitAfterRaiseMinor instead).
    """

    @property
    def name(self) -> str:
        return "rebid.invite_after_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 165

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_minor,
            Not(Balanced(), label="balanced/semi-balanced"),
            BergenPtsRange(_my_opening_suit, min_pts=16, max_pts=18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"16-18 Bergen pts, invitational raise — 3{suit.letter}",
        )


class Rebid5mAfterLimitRaiseMinor(Rule):
    """Bid 5 of minor after limit raise — 15+ Bergen pts, unbalanced, 6+ minor.

    e.g. 1D→3D→5D
    """

    @property
    def name(self) -> str:
        return "rebid.5m_after_limit_raise_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 180

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_limit_raised,
            _opening_suit_is_minor,
            Not(Balanced(), label="balanced/semi-balanced"),
            _has_rebiddable_suit,
            BergenPtsRange(_my_opening_suit, min_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"15+ Bergen pts, 6+ minor, unbalanced — SAYC 5{suit.letter}",
        )


class RebidAcceptLimitRaiseMinor3NT(Rule):
    """Bid 3NT after limit raise of minor — unbalanced, 15+ Bergen pts.

    e.g. 1D→3D→3NT

    Covers the gap where opener accepts a minor limit raise but is
    unbalanced with fewer than 6 cards in the minor. With 25+ combined
    points (opener 15+ Bergen + responder 10-12), game is reached.
    3NT is the default game contract with a minor fit since 5m requires
    11 tricks. Balanced hands are already handled by
    Rebid3NTAfterRaiseMinor; hands with 6+ minor go to
    Rebid5mAfterLimitRaiseMinor.
    """

    @property
    def name(self) -> str:
        return "rebid.accept_limit_raise_minor_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 178

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_limit_raised,
            _opening_suit_is_minor,
            Not(Balanced(), label="balanced/semi-balanced"),
            BergenPtsRange(_my_opening_suit, min_pts=15),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15+ Bergen pts, unbalanced, accept limit raise — 3NT",
        )


# ── Rules — After 1NT Response ──────────────────────────────────────


class Rebid3NTOver1NT(Rule):
    """3NT over 1NT — 19-21 HCP, balanced.

    e.g. 1H→1NT→3NT

    SAYC: "19-21 HCP, balanced."
    """

    @property
    def name(self) -> str:
        return "rebid.3nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 360

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_1nt, Balanced(), HcpRange(19, 21))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="19-21 HCP balanced — SAYC 3NT over 1NT",
        )


class RebidJumpShiftOver1NT(Rule):
    """Jump in new suit over 1NT — 19-21 total pts, 4+ card second suit.

    e.g. 1H→1NT→3C

    SAYC: "Jump in new suit; 19-21 points, 4+ cards; forcing."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_shift_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_for_rebid, "4+ card new suit")

    @property
    def priority(self) -> int:
        return 340

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_1nt,
            TotalPtsRange(19, 21),
            Not(Balanced(), label="balanced/semi-balanced"),
            self._new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        resp = _partner_response(ctx)
        bid = _jump_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"19-21 pts, jump shift — SAYC {bid}, forcing",
            forcing=True,
        )


class Rebid2NTOver1NT(Rule):
    """2NT over 1NT — 18-19 HCP, balanced; invitational.

    e.g. 1S→1NT→2NT

    SAYC: "18-19 HCP, balanced; invitational."
    """

    @property
    def name(self) -> str:
        return "rebid.2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 250

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_1nt, Balanced(), HcpRange(18, 19))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="18-19 HCP balanced — SAYC 2NT over 1NT, invitational",
        )


class RebidJumpRebidOver1NT(Rule):
    """Jump rebid own suit over 1NT — 6+ cards, 17-18 total pts.

    e.g. 1H→1NT→3H

    SAYC: "6+ card suit, 17-18 points; invitational."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_rebid_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 230

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_1nt,
            _has_rebiddable_suit,
            TotalPtsRange(17, 18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"6+ card {suit.letter}, 17-18 pts — SAYC jump rebid over 1NT"
            ),
        )


class RebidGameOver1NT(Rule):
    """Bid 4M over 1NT — 6+ card major, 19-21 total pts.

    e.g. 1H->1NT->4H, 1S->1NT->4S

    Majors only -- with a long minor, prefer 3NT or a jump shift.

    SAYC: "Double-jump rebid own suit; self-supporting 6+ cards, 19-21 pts."
    """

    @property
    def name(self) -> str:
        return "rebid.game_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 275

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_1nt,
            _opening_suit_is_major,
            _has_rebiddable_suit,
            TotalPtsRange(19, 21),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"19-21 pts, 6+ card {suit.letter} — SAYC double-jump rebid over 1NT"
            ),
        )


class RebidNewLowerSuitOver1NT(Rule):
    """Bid 2 of a lower new suit over 1NT — 4+ cards, non-forcing.

    e.g. 1S→1NT→2C, 1H→1NT→2D

    SAYC: "2 of a lower new suit; 4+ cards; non-forcing."
    """

    @property
    def name(self) -> str:
        return "rebid.new_lower_suit_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._lower_suit = Computed(_find_lower_new_suit, "4+ card lower new suit")

    @property
    def priority(self) -> int:
        return 150

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_1nt,
            TotalPtsRange(max_pts=18),
            self._lower_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._lower_suit.value
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=(
                f"4+ card {suit.letter}, lower suit — SAYC 2{suit.letter} over 1NT"
            ),
        )


class RebidSuitOver1NT(Rule):
    """Rebid 2 of own suit over 1NT — 6+ cards, minimum.

    e.g. 1H→1NT→2H

    SAYC: "2 of original suit; 6+ cards; non-forcing."
    """

    @property
    def name(self) -> str:
        return "rebid.rebid_suit_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 130

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_1nt,
            _has_rebiddable_suit,
            TotalPtsRange(max_pts=16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=(
                f"6+ card {suit.letter}, minimum — SAYC 2{suit.letter} over 1NT"
            ),
        )


class RebidPassOver1NT(Rule):
    """Pass over 1NT — balanced minimum.

    e.g. 1D→1NT→Pass

    SAYC: "Balanced minimum; pass."
    """

    @property
    def name(self) -> str:
        return "rebid.pass_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 50

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_1nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Balanced minimum — pass over 1NT",
        )


# ── Rules — After New Suit at 1-Level ───────────────────────────────


class RebidJumpTo2NT(Rule):
    """Jump to 2NT — 18-19 HCP, balanced.

    e.g. 1D→1S→2NT

    SAYC: "Jump to 2NT — 18-19 HCP, balanced."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_to_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 380

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            Balanced(),
            HcpRange(18, 19),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="18-19 HCP balanced — SAYC jump to 2NT",
        )


class RebidJumpShiftNewSuit(Rule):
    """Jump shift into second suit — 19-21 total pts, 4+ cards; forcing.

    e.g. 1H→1S→3C, 1D→1H→3C

    SAYC: "Jump shift into second suit — 19-21 points, 4+ cards; forcing."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_shift_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_for_rebid, "4+ card new suit")

    @property
    def priority(self) -> int:
        return 370

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            TotalPtsRange(19, 21),
            Not(Balanced(), label="balanced/semi-balanced"),
            self._new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        resp = _partner_response(ctx)
        bid = _jump_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"19-21 pts, jump shift in {suit.letter} — forcing",
            forcing=True,
        )


class RebidJumpRaiseResponder(Rule):
    """Jump raise responder's suit — 4-card support, 17-18 total pts.

    e.g. 1D→1H→3H, 1C→1S→3S

    SAYC: "Jump raise responder's suit — 4-card support, 17-18 points."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_raise_responder"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 280

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            HasSuitFit(_responder_suit, min_len=4),
            TotalPtsRange(17, 18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp_suit = _partner_response(ctx).suit
        return RuleResult(
            bid=SuitBid(3, resp_suit),
            rule_name=self.name,
            explanation=(
                f"4+ card support, 17-18 pts — SAYC jump raise to 3{resp_suit.letter}"
            ),
        )


class RebidReverse(Rule):
    """Reverse — new suit ranking higher than opening suit, 17+ total pts.

    e.g. 1D→1S→2H, 1C→1S→2D

    SAYC: "New suit ranking higher than first suit at the 2-level —
    requires 17+ points.  First suit must be longer than second."
    """

    @property
    def name(self) -> str:
        return "rebid.reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._reverse_suit = Computed(_find_reverse_suit, "reverse suit")

    @property
    def priority(self) -> int:
        return 260

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            TotalPtsRange(min_pts=17),
            self._reverse_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._reverse_suit.value
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=(f"17+ pts, {suit.letter} reverse — SAYC, forcing one round"),
            forcing=True,
        )


class RebidJumpRebidOwnSuit(Rule):
    """Jump rebid own suit — 6+ cards, 17-18 total pts.

    e.g. 1H→1S→3H, 1D→1H→3D

    SAYC: "Jump rebid own suit — 6+ cards, 17-18 points."
    """

    @property
    def name(self) -> str:
        return "rebid.jump_rebid_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 240

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            _has_rebiddable_suit,
            TotalPtsRange(17, 18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"6+ card {suit.letter}, 17-18 pts — SAYC jump rebid",
        )


class RebidRaiseResponder(Rule):
    """Raise responder's suit at cheapest level — 4-card support, 12-16 total pts.

    e.g. 1D→1H→2H, 1C→1S→2S

    SAYC: "Raise responder's suit at cheapest level — 4-card support, minimum."
    """

    @property
    def name(self) -> str:
        return "rebid.raise_responder"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 160

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            HasSuitFit(_responder_suit, min_len=4),
            TotalPtsRange(12, 16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp_suit = _partner_response(ctx).suit
        return RuleResult(
            bid=SuitBid(2, resp_suit),
            rule_name=self.name,
            explanation=(
                f"4+ card support, minimum — SAYC raise to 2{resp_suit.letter}"
            ),
        )


class RebidNewSuitNonreverse(Rule):
    """Bid new suit at cheapest level — non-reverse, minimum.

    e.g. 1H→1S→2C, 1D→1H→1S

    SAYC: "Bid new suit at cheapest level — 4+ cards, new suit ranks
    lower than first suit (non-reverse).  Minimum."
    """

    @property
    def name(self) -> str:
        return "rebid.new_suit_nonreverse"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._nonrev_suit = Computed(
            _find_nonreverse_new_suit, "non-reverse new suit (4+)"
        )

    @property
    def priority(self) -> int:
        return 140

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            TotalPtsRange(max_pts=18),
            self._nonrev_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._nonrev_suit.value
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"4+ card {suit.letter}, non-reverse — SAYC {bid}",
        )


class RebidOwnSuit(Rule):
    """Rebid own suit at cheapest level — 6+ cards, minimum.

    e.g. 1H→1S→2H, 1S→2C→2S

    SAYC: "Rebid own suit at cheapest level — 6+ cards, minimum."
    Also applies after 2-over-1 responses.
    """

    @property
    def name(self) -> str:
        return "rebid.rebid_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 120

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            Any(_partner_bid_new_suit_1_level, _partner_bid_2_over_1),
            _has_rebiddable_suit,
            TotalPtsRange(max_pts=16),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6+ card {suit.letter}, minimum — SAYC {bid}",
        )


class Rebid1NT(Rule):
    """Rebid 1NT — 12-14 HCP, balanced.

    e.g. 1D→1H→1NT, 1C→1S→1NT

    SAYC: "12-14 HCP, balanced, no other descriptive bid."
    """

    @property
    def name(self) -> str:
        return "rebid.1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 100

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            Balanced(strict=True),
            HcpRange(12, 14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12-14 HCP balanced — SAYC 1NT rebid",
        )


# ── Rules — After 2-Over-1 Response ─────────────────────────────────


class RebidRaise2Over1Responder(Rule):
    """Raise 2-over-1 responder's suit — 4-card support.

    e.g. 1S→2C→3C, 1H→2D→3D

    SAYC: "Raise responder's suit — 4-card support."
    """

    @property
    def name(self) -> str:
        return "rebid.raise_2over1_responder"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 290

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_2_over_1,
            HasSuitFit(_responder_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp_suit = _partner_response(ctx).suit
        return RuleResult(
            bid=SuitBid(3, resp_suit),
            rule_name=self.name,
            explanation=(
                f"4+ card support — SAYC raise to 3{resp_suit.letter} after 2-over-1"
            ),
        )


class RebidNewSuitAfter2Over1(Rule):
    """Bid a new (third) suit after 2-over-1 — 4+ cards.

    e.g. 1S→2C→2D, 1H→2C→2D

    SAYC: "New suit — 4+ cards, natural."
    """

    @property
    def name(self) -> str:
        return "rebid.new_suit_after_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_for_rebid, "4+ card new suit")

    @property
    def priority(self) -> int:
        return 270

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_2_over_1, self._new_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"4+ card {suit.letter} — SAYC new suit after 2-over-1",
            forcing=True,
        )


class RebidSuitAfter2Over1(Rule):
    """Rebid own suit after 2-over-1 — 6+ cards.

    e.g. 1H→2C→2H, 1S→2D→2S

    SAYC: "Rebid own suit — 6+ cards."
    """

    @property
    def name(self) -> str:
        return "rebid.rebid_suit_after_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 190

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_2_over_1, _has_rebiddable_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6+ card {suit.letter} — SAYC rebid after 2-over-1",
        )


class Rebid2NTAfter2Over1(Rule):
    """Bid 2NT after 2-over-1 — 12-14 HCP, balanced.

    e.g. 1H→2C→2NT, 1S→2D→2NT

    SAYC: "Cheapest NT — balanced minimum (12-14)."
    """

    @property
    def name(self) -> str:
        return "rebid.nt_after_2over1_min"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 110

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_2_over_1,
            Balanced(),
            HcpRange(12, 14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12-14 HCP balanced — SAYC 2NT after 2-over-1",
        )


class Rebid3NTAfter2Over1(Rule):
    """Bid 3NT after 2-over-1 — 18-19 HCP, balanced.

    e.g. 1H→2C→3NT, 1S→2D→3NT

    SAYC: "Jump rebid — extra values."
    """

    @property
    def name(self) -> str:
        return "rebid.nt_after_2over1_max"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 200

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_2_over_1,
            Balanced(),
            HcpRange(18, 19),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="18-19 HCP balanced — SAYC 3NT after 2-over-1",
        )


# ── Rules — Pass After Game-Level Responses (A1) ─────────────────


class RebidPassAfter3NT(Rule):
    """Pass after partner bids 3NT.

    e.g. 1H→3NT→Pass, 1D→3NT→Pass

    Partner's 3NT is to play (15-17 HCP balanced over major,
    16-18 HCP balanced over minor). No reason to disturb.
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 55

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_3nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Partner bid 3NT to play — pass",
        )


class RebidPassAfterGameRaise(Rule):
    """Pass after partner's preemptive game raise (4M).

    e.g. 1H→4H→Pass, 1S→4S→Pass

    Partner bid 4M with 5+ trumps and a weak hand. Game is reached.
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_game_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 56

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_game_raise)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Partner bid game preemptively — pass",
        )


# ── Rules — After Jacoby 2NT (A2) ────────────────────────────────


class RebidJacoby3LevelShortness(Rule):
    """Show shortness at the 3-level after Jacoby 2NT.

    e.g. 1H→2NT→3D (singleton/void in diamonds)

    Bid 3 of the suit where opener has a singleton or void.
    Most descriptive rebid — always show shortness when you have it.
    """

    @property
    def name(self) -> str:
        return "rebid.jacoby_3level_shortness"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._shortness = Computed(
            _find_shortness_suit, "shortness (singleton or void)"
        )

    @property
    def priority(self) -> int:
        return 440

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_jacoby_2nt, self._shortness)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._shortness.value
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"Jacoby 2NT — showing shortness (singleton or void) in {suit.letter}"
            ),
            forcing=True,
        )


class RebidJacoby4LevelSource(Rule):
    """Show a 5+ card side suit at the 4-level after Jacoby 2NT.

    e.g. 1H→2NT→4C (5+ clubs, source of tricks)

    Bid 4 of the suit where opener has a source of tricks.
    """

    @property
    def name(self) -> str:
        return "rebid.jacoby_4level_source"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._side_suit = Computed(_find_5_card_side_suit, "5+ card side suit")

    @property
    def priority(self) -> int:
        return 430

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_jacoby_2nt, self._side_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._side_suit.value
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(f"Jacoby 2NT — showing 5+ card {suit.letter} side suit"),
            forcing=True,
        )


class RebidJacoby3Major(Rule):
    """Rebid 3M after Jacoby 2NT — maximum, no shortness, no side source.

    e.g. 1H→2NT→3H (18+ pts, slam interest)

    18+ total points, slam interest.
    """

    @property
    def name(self) -> str:
        return "rebid.jacoby_3major"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 420

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_jacoby_2nt,
            Not(_has_shortness),
            Not(_has_side_suit),
            TotalPtsRange(min_pts=18),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"Jacoby 2NT — 18+ pts, no shortness"
                f" — SAYC 3{suit.letter}, slam interest"
            ),
            forcing=True,
        )


class RebidJacoby3NT(Rule):
    """Rebid 3NT after Jacoby 2NT — medium, no shortness, no side source.

    e.g. 1H→2NT→3NT (15-17 pts)

    15-17 total points.
    """

    @property
    def name(self) -> str:
        return "rebid.jacoby_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 410

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_jacoby_2nt,
            Not(_has_shortness),
            Not(_has_side_suit),
            TotalPtsRange(15, 17),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Jacoby 2NT — 15-17 pts, no shortness — SAYC 3NT",
            forcing=True,
        )


class RebidJacoby4Major(Rule):
    """Rebid 4M after Jacoby 2NT — minimum, no shortness, sign-off.

    e.g. 1H→2NT→4H (12-14 pts, sign-off)

    12-14 total points.
    """

    @property
    def name(self) -> str:
        return "rebid.jacoby_4major"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 400

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_jacoby_2nt,
            Not(_has_shortness),
            Not(_has_side_suit),
            TotalPtsRange(max_pts=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"Jacoby 2NT — minimum, no shortness — SAYC 4{suit.letter}, sign-off"
            ),
        )


# ── Rules — After 2NT Over Minor (A3) ────────────────────────────


class RebidShowMajorAfter2NTMinor(Rule):
    """Show a 4-card major after 1m→2NT.

    e.g. 1D→2NT→3H, 1C→2NT→3S

    2NT is game forcing (13-15 HCP balanced), but a 4-4 major fit
    usually plays better than 3NT. Bid 3H or 3S to check for a fit
    before settling in notrump. With both majors, bid 3H first -
    responder can bid 3S with 4 spades or 3NT without a heart fit.
    """

    @property
    def name(self) -> str:
        return "rebid.show_major_after_2nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 395

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_2nt_over_minor, _has_4_card_major)

    def select(self, ctx: BiddingContext) -> RuleResult:
        # With both 4-card majors, bid hearts first
        suit = Suit.HEARTS if ctx.hand.num_hearts >= 4 else Suit.SPADES
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(f"4+ card {suit.letter} after 1m→2NT — SAYC 3{suit.letter}"),
            forcing=True,
        )


class RebidMinorAfter2NTMinor(Rule):
    """Rebid 3 of own minor after 1m→2NT — 6+ cards, no 4-card major.

    e.g. 1D→2NT→3D, 1C→2NT→3C
    """

    @property
    def name(self) -> str:
        return "rebid.minor_after_2nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 392

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_2nt_over_minor,
            _no_4_card_major,
            _has_rebiddable_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"6+ card {suit.letter}, no 4-card major"
                f" — SAYC 3{suit.letter} after 2NT"
            ),
            forcing=True,
        )


class RebidNTAfter2NTMinor(Rule):
    """Bid 3NT after 1m→2NT — balanced catch-all.

    e.g. 1D→2NT→3NT, 1C→2NT→3NT
    """

    @property
    def name(self) -> str:
        return "rebid.nt_after_2nt_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 390

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_bid_2nt_over_minor)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No 4-card major, no long minor — SAYC 3NT after 2NT",
        )


# ── Rules — After Jump Shift (A4) ────────────────────────────────


class RebidRaiseAfterJumpShift(Rule):
    """Raise responder's suit after a jump shift — 4+ card support.

    e.g. 1D→2S→3S, 1H→3C→4C
    """

    @property
    def name(self) -> str:
        return "rebid.raise_after_jump_shift"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 460

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_jump_shifted,
            HasSuitFit(_responder_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(resp.suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=(
                f"4+ card support for {resp.suit.letter} — raise after jump shift"
            ),
            forcing=True,
        )


class RebidOwnSuitAfterJumpShift(Rule):
    """Rebid own suit after a jump shift — 6+ cards.

    e.g. 1H→3C→3H, 1D→2S→3D
    """

    @property
    def name(self) -> str:
        return "rebid.own_suit_after_jump_shift"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 455

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_jump_shifted, _has_rebiddable_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=(f"6+ card {suit.letter} — rebid after jump shift"),
            forcing=True,
        )


class RebidNewSuitAfterJumpShift(Rule):
    """Bid a new (third) suit after a jump shift — 4+ cards.

    e.g. 1H→3C→3D, 1D→2S→3C
    """

    @property
    def name(self) -> str:
        return "rebid.new_suit_after_jump_shift"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._new_suit = Computed(_find_new_suit_for_rebid, "4+ card new suit")

    @property
    def priority(self) -> int:
        return 450

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_jump_shifted, self._new_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=(f"4+ card {suit.letter} — new suit after jump shift"),
            forcing=True,
        )


class RebidNTAfterJumpShift(Rule):
    """Bid NT after a jump shift — balanced catch-all.

    e.g. 1H→2S→2NT, 1D→3C→3NT
    """

    @property
    def name(self) -> str:
        return "rebid.nt_after_jump_shift"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 445

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1_suit, _partner_jump_shifted)

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(Suit.NOTRUMP, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation="Balanced — NT after jump shift",
            forcing=True,
        )


# ── Rules — Help Suit Game Try (A5) ──────────────────────────────


class RebidHelpSuitGameTry(Rule):
    """Bid a new suit as a help suit game try after 1M→2M.

    e.g. 1H→2H→2S, 1S→2S→3D

    16-18 Bergen pts, major raise only. Bids the weakest side suit
    to ask responder about help.
    """

    @property
    def name(self) -> str:
        return "rebid.help_suit_game_try"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    def __init__(self) -> None:
        self._help_suit = Computed(
            _find_help_suit, "help suit (weak 3+ card side suit)"
        )

    @property
    def priority(self) -> int:
        return 215

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_single_raised,
            _opening_suit_is_major,
            BergenPtsRange(_my_opening_suit, min_pts=16, max_pts=18),
            self._help_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._help_suit.value
        resp = _partner_response(ctx)
        bid = cheapest_bid_in_suit(suit, resp)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=(
                f"16-18 Bergen pts, help suit game try"
                f" — asking for help in {suit.letter}"
            ),
            forcing=True,
        )


# ── Rules — Double-Jump Bids After New Suit 1-Level (A6) ─────────


class RebidDoubleJumpRaiseResponder(Rule):
    """Double-jump raise of responder's suit — 19-21 total pts, 4+ support.

    e.g. 1D→1H→4H, 1C→1S→4S

    Fast arrival to game — strong enough to bid game but not enough to
    explore slam. With 22+ opener would have opened 2C.
    """

    @property
    def name(self) -> str:
        return "rebid.double_jump_raise_responder"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 385

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            HasSuitFit(_responder_suit, min_len=4),
            TotalPtsRange(19, 21),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        resp_suit = _partner_response(ctx).suit
        return RuleResult(
            bid=SuitBid(4, resp_suit),
            rule_name=self.name,
            explanation=(
                f"19-21 pts, 4+ card support — double-jump to 4{resp_suit.letter}"
            ),
        )


class RebidDoubleJumpRebidOwnSuit(Rule):
    """Double-jump rebid own suit — 19-21 total pts, 6+ self-supporting suit.

    e.g. 1H→1S→4H, 1D→1H→5D

    Fast arrival to game — strong enough to bid game but not enough to
    explore slam. With 22+ opener would have opened 2C.
    """

    @property
    def name(self) -> str:
        return "rebid.double_jump_rebid_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 383

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1_suit,
            _partner_bid_new_suit_1_level,
            _has_rebiddable_suit,
            TotalPtsRange(19, 21),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _my_opening_suit(ctx)
        level = 4 if suit.is_major else 5
        return RuleResult(
            bid=SuitBid(level, suit),
            rule_name=self.name,
            explanation=(
                f"19-21 pts, 6+ card {suit.letter}"
                f" — double-jump to {level}{suit.letter}"
            ),
        )
