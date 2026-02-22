"""Responses to 1NT and 2NT openings -- SAYC.

Response rules for when partner opens 1NT (15-17 HCP balanced) or
2NT (20-21 HCP balanced). Conventions: Stayman, Jacoby Transfers,
Texas Transfers, Gerber, puppet to minor sign-off.
"""

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import Suit

# -- Helpers -----------------------------------------------------------------


def _opened_1nt(ctx: BiddingContext) -> bool:
    """Whether partner opened 1NT."""
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 1 and bid.suit == Suit.NOTRUMP


def _opened_2nt(ctx: BiddingContext) -> bool:
    """Whether partner opened 2NT."""
    if ctx.opening_bid is None:
        return False
    _, bid = ctx.opening_bid
    return is_suit_bid(bid) and bid.level == 2 and bid.suit == Suit.NOTRUMP


def _has_5_plus_major(ctx: BiddingContext) -> bool:
    """Whether responder has a 5+ card major."""
    return ctx.hand.num_hearts >= 5 or ctx.hand.num_spades >= 5


def _is_4333(ctx: BiddingContext) -> bool:
    """Whether responder has 4-3-3-3 flat shape."""
    return ctx.sorted_shape == (4, 3, 3, 3)


def _longest_major(ctx: BiddingContext) -> Suit:
    """Return the longer major; spades with equal length."""
    if ctx.hand.num_hearts > ctx.hand.num_spades:
        return Suit.HEARTS
    return Suit.SPADES


def _longest_minor(ctx: BiddingContext) -> Suit:
    """Return the longer minor; diamonds with equal length."""
    if ctx.hand.num_clubs > ctx.hand.num_diamonds:
        return Suit.CLUBS
    return Suit.DIAMONDS


# -- Slam-level responses ---------------------------------------------------


class RespondGerber(Rule):
    """Gerber 4C -- ace-asking over 1NT.

    18+ HCP, balanced, no 5+ card major. Asks opener for aces.
    SAYC 4C directly over NT is Gerber (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "response.gerber"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 495

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        if _has_5_plus_major(ctx):
            return False
        return ctx.hcp >= 18 and (ctx.is_balanced or ctx.is_semi_balanced)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.CLUBS),
            rule_name=self.name,
            explanation="18+ HCP, balanced -- Gerber ace-ask over 1NT",
            alerts=("Gerber -- asking for aces",),
        )


class Respond4NTOver1NT(Rule):
    """Quantitative 4NT -- invites 6NT.

    15-17 HCP, balanced. Opener passes with minimum (15), bids 6NT with
    maximum (16-17). SAYC quantitative (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "response.4nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 485

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        return 15 <= ctx.hcp <= 17 and (ctx.is_balanced or ctx.is_semi_balanced)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="15-17 HCP, balanced -- quantitative 4NT, invites 6NT",
        )


class Respond3MajorOver1NT(Rule):
    """3H or 3S -- 6+ card major, slam interest.

    Shows a strong hand (16+ HCP) with a 6+ card major. Forcing,
    slam interest. SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.3_major_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 475

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        if ctx.hcp < 16:
            return False
        return ctx.hand.num_hearts >= 6 or ctx.hand.num_spades >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"6+ {suit.letter}, 16+ HCP -- slam interest over 1NT",
            forcing=True,
        )


class RespondTexasTransfer(Rule):
    """Texas transfer -- 4D (hearts) or 4H (spades).

    6+ card major, 10-15 HCP. Game-level sign-off; opener completes
    the transfer. SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.texas_transfer"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 465

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        if not (10 <= ctx.hcp <= 15):
            return False
        return ctx.hand.num_hearts >= 6 or ctx.hand.num_spades >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        # Transfer one step below: 4D -> hearts, 4H -> spades
        transfer_suit = Suit.DIAMONDS if suit == Suit.HEARTS else Suit.HEARTS
        return RuleResult(
            bid=SuitBid(4, transfer_suit),
            rule_name=self.name,
            explanation=(
                f"6+ {suit.letter}, game values -- Texas transfer to 4{suit.letter}"
            ),
            alerts=(f"Texas transfer -- showing 6+ {suit.letter}",),
        )


# -- Convention-level responses ----------------------------------------------


class RespondStayman(Rule):
    """Stayman 2C -- asks opener for a 4-card major.

    Requirements (research/05-conventions.md):
    - 8+ HCP with at least one 4-card major, not 4-3-3-3 flat, no 5+ major
    - OR garbage Stayman: 4-4+ in both majors with any HCP (plan to pass)
    - Should NOT be used with 4-3-3-3 shape (prefer 2NT/3NT)
    """

    @property
    def name(self) -> str:
        return "response.stayman"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 445

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        has_4h = ctx.hand.num_hearts >= 4
        has_4s = ctx.hand.num_spades >= 4
        # Garbage Stayman: 4-4+ in majors, any HCP
        if has_4h and has_4s:
            return True
        # Regular Stayman: 8+ HCP, 4-card major, no 5+ major, not 4-3-3-3
        if ctx.hcp >= 8 and (has_4h or has_4s):
            if _has_5_plus_major(ctx):
                return False
            return not _is_4333(ctx)
        return False

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.CLUBS),
            rule_name=self.name,
            explanation="Stayman -- asking for 4-card major over 1NT",
            alerts=("Stayman -- asking for 4-card major",),
        )


class RespondJacobyTransfer(Rule):
    """Jacoby transfer -- 2D (5+ hearts) or 2H (5+ spades).

    Any strength. Opener completes the transfer (or super-accepts with
    17 HCP and 4+ support). SAYC (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "response.jacoby_transfer"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 435

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        return _has_5_plus_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        # Transfer one step below: 2D -> hearts, 2H -> spades
        transfer_suit = Suit.DIAMONDS if suit == Suit.HEARTS else Suit.HEARTS
        return RuleResult(
            bid=SuitBid(2, transfer_suit),
            rule_name=self.name,
            explanation=f"5+ {suit.letter} -- Jacoby transfer over 1NT",
            alerts=(f"Transfer -- showing 5+ {suit.letter}",),
        )


# -- Game-level responses ---------------------------------------------------


class Respond3NTOver1NT(Rule):
    """3NT -- to play.

    10-15 HCP. Sign-off. Hands with 4-card majors and non-flat shape
    will Stayman instead (higher priority).
    SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 425

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        return 10 <= ctx.hcp <= 15

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-15 HCP -- 3NT to play over 1NT",
        )


# -- Invitational responses -------------------------------------------------


class Respond3MinorOver1NT(Rule):
    """3C or 3D -- 6+ card minor, invitational.

    8-9 HCP, 6+ card minor suit. Invites 3NT; opener passes with
    minimum or bids 3NT with maximum. SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.3_minor_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 415

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        if not (8 <= ctx.hcp <= 9):
            return False
        return ctx.hand.num_clubs >= 6 or ctx.hand.num_diamonds >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_minor(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"6+ {suit.letter}, 8-9 HCP -- invitational 3{suit.letter} over 1NT"
            ),
        )


class Respond2NTOver1NT(Rule):
    """2NT -- invitational to 3NT.

    8-9 HCP, balanced. Opener passes with minimum (15) or bids 3NT
    with maximum (16-17). SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 405

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        return 8 <= ctx.hcp <= 9

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8-9 HCP -- invitational 2NT over 1NT",
        )


# -- Weak responses ----------------------------------------------------------


class Respond2SPuppet(Rule):
    """2S puppet to 3C -- sign-off mechanism for weak hands with long minors.

    Weak hand (0-7 HCP), 6+ card minor. Opener must bid 3C; responder
    passes (clubs) or corrects to 3D (diamonds).
    SAYC (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "response.2s_puppet"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 395

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        if ctx.hcp > 7:
            return False
        return ctx.hand.num_clubs >= 6 or ctx.hand.num_diamonds >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.SPADES),
            rule_name=self.name,
            explanation="Weak hand, 6+ minor -- 2S puppet to 3C over 1NT",
            alerts=("Puppet to 3C -- weak hand with long minor",),
        )


class RespondPassOver1NT(Rule):
    """Pass -- no game interest, no reason to disturb 1NT.

    0-7 HCP without a 5+ major (would transfer), 6+ minor (would puppet),
    or 4-4 majors (would garbage Stayman).
    """

    @property
    def name(self) -> str:
        return "response.pass_over_1nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 45

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt(ctx):
            return False
        return ctx.hcp <= 7

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="0-7 HCP -- pass 1NT",
        )


# ══════════════════════════════════════════════════════════════════════
# Responses to 2NT opening (20-21 HCP balanced)
# ══════════════════════════════════════════════════════════════════════


class RespondGerberOver2NT(Rule):
    """Gerber 4C -- ace-asking over 2NT.

    e.g. 2NT->4C

    13+ HCP, balanced, no 5+ card major. Asks opener for aces.
    SAYC 4C directly over NT is Gerber (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "response.gerber_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 494

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        if _has_5_plus_major(ctx):
            return False
        return ctx.hcp >= 13 and (ctx.is_balanced or ctx.is_semi_balanced)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.CLUBS),
            rule_name=self.name,
            explanation="13+ HCP, balanced -- Gerber ace-ask over 2NT",
            alerts=("Gerber -- asking for aces",),
        )


class Respond4NTOver2NT(Rule):
    """Quantitative 4NT -- invites 6NT.

    e.g. 2NT->4NT

    11-12 HCP, balanced. Opener passes with minimum (20), bids 6NT with
    maximum (21). SAYC quantitative (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "response.4nt_over_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 484

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        return 11 <= ctx.hcp <= 12 and (ctx.is_balanced or ctx.is_semi_balanced)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="11-12 HCP, balanced -- quantitative 4NT, invites 6NT over 2NT",
        )


class RespondTexasOver2NT(Rule):
    """Texas transfer -- 4D (hearts) or 4H (spades) over 2NT.

    e.g. 2NT->4D (transfer to 4H), 2NT->4H (transfer to 4S)

    6+ card major, 4-10 HCP. Game-level sign-off; opener completes
    the transfer. SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.texas_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 464

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        if not (4 <= ctx.hcp <= 10):
            return False
        return ctx.hand.num_hearts >= 6 or ctx.hand.num_spades >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        transfer_suit = Suit.DIAMONDS if suit == Suit.HEARTS else Suit.HEARTS
        return RuleResult(
            bid=SuitBid(4, transfer_suit),
            rule_name=self.name,
            explanation=(
                f"6+ {suit.letter}, game values -- Texas transfer to 4{suit.letter}"
                " over 2NT"
            ),
            alerts=(f"Texas transfer -- showing 6+ {suit.letter}",),
        )


class RespondStaymanOver2NT(Rule):
    """Stayman 3C -- asks opener for a 4-card major over 2NT.

    e.g. 2NT->3C

    4+ HCP, at least one 4-card major, not 4-3-3-3 flat, no 5+ major.
    No garbage Stayman over 2NT (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "response.stayman_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 444

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        if ctx.hcp < 4:
            return False
        has_4h = ctx.hand.num_hearts >= 4
        has_4s = ctx.hand.num_spades >= 4
        if not (has_4h or has_4s):
            return False
        if _has_5_plus_major(ctx):
            return False
        return not _is_4333(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.CLUBS),
            rule_name=self.name,
            explanation="Stayman -- asking for 4-card major over 2NT",
            alerts=("Stayman -- asking for 4-card major",),
        )


class RespondTransferOver2NT(Rule):
    """Jacoby transfer -- 3D (5+ hearts) or 3H (5+ spades) over 2NT.

    e.g. 2NT->3D (transfer to 3H), 2NT->3H (transfer to 3S)

    Any strength. Opener completes the transfer.
    SAYC (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "response.transfer_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 434

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        return _has_5_plus_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _longest_major(ctx)
        transfer_suit = Suit.DIAMONDS if suit == Suit.HEARTS else Suit.HEARTS
        return RuleResult(
            bid=SuitBid(3, transfer_suit),
            rule_name=self.name,
            explanation=f"5+ {suit.letter} -- transfer over 2NT",
            alerts=(f"Transfer -- showing 5+ {suit.letter}",),
        )


class Respond3NTOver2NT(Rule):
    """3NT -- to play over 2NT.

    e.g. 2NT->3NT

    4-10 HCP. Sign-off. Hands with 4-card majors and non-flat shape
    will Stayman instead (higher priority).
    SAYC (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "response.3nt_over_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 424

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        return 4 <= ctx.hcp <= 10

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="4-10 HCP -- 3NT to play over 2NT",
        )


class Respond3SPuppetOver2NT(Rule):
    """3S puppet to 4C -- sign-off mechanism for weak hands with long minors.

    e.g. 2NT->3S

    Weak hand (0-3 HCP), 6+ card minor. Opener must bid 4C; responder
    passes (clubs) or corrects to 4D (diamonds).
    SAYC (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "response.3s_puppet_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 394

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        if ctx.hcp > 3:
            return False
        return ctx.hand.num_clubs >= 6 or ctx.hand.num_diamonds >= 6

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.SPADES),
            rule_name=self.name,
            explanation="Weak hand, 6+ minor -- 3S puppet to 4C over 2NT",
            alerts=("Puppet to 4C -- weak hand with long minor",),
        )


class RespondPassOver2NT(Rule):
    """Pass -- no game interest over 2NT.

    e.g. 2NT->Pass

    0-3 HCP without a 6+ minor (would puppet).
    """

    @property
    def name(self) -> str:
        return "response.pass_over_2nt"

    @property
    def category(self) -> Category:
        return Category.RESPONSE

    @property
    def priority(self) -> int:
        return 44

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_2nt(ctx):
            return False
        return ctx.hcp <= 3

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="0-3 HCP -- pass 2NT",
        )
