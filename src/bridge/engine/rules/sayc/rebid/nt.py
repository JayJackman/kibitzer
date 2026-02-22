"""Opener's rebid rules after 1NT opening -- SAYC.

All rebid rules for when I opened 1NT (15-17 HCP balanced) and partner
has responded. Covers:
- Stayman responses (2D/2H/2S)
- Jacoby transfer completion (normal + super-accept)
- 2S puppet completion (3C)
- Gerber ace response (4D/4H/4S/4NT)
- Texas transfer completion (4H/4S)
- Raises/declines for 3M, 2NT, 3m, 3NT, 4NT

All rules belong to Category.REBID_OPENER.
"""

from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Rank, Suit

# -- Helpers -----------------------------------------------------------------


def _opened_1nt_self(ctx: BiddingContext) -> bool:
    """Whether I opened 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 1 and bid.suit == Suit.NOTRUMP


def _partner_bid(ctx: BiddingContext) -> SuitBid:
    """Partner's response (always a SuitBid in rebid phase after 1NT)."""
    resp = ctx.partner_last_bid
    assert resp is not None and is_suit_bid(resp)
    return resp


def _partner_bid_stayman(ctx: BiddingContext) -> bool:
    """Partner bid 2C (Stayman)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit == Suit.CLUBS


def _partner_transferred(ctx: BiddingContext) -> bool:
    """Partner bid 2D (hearts) or 2H (spades) -- Jacoby transfer."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit in (Suit.DIAMONDS, Suit.HEARTS)


def _transfer_suit(ctx: BiddingContext) -> Suit:
    """The suit partner transferred to (hearts if 2D, spades if 2H)."""
    resp = _partner_bid(ctx)
    if resp.suit == Suit.DIAMONDS:
        return Suit.HEARTS
    return Suit.SPADES


def _partner_bid_2s_puppet(ctx: BiddingContext) -> bool:
    """Partner bid 2S (puppet to 3C)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit == Suit.SPADES


def _partner_bid_gerber(ctx: BiddingContext) -> bool:
    """Partner bid 4C (Gerber)."""
    resp = _partner_bid(ctx)
    return resp.level == 4 and resp.suit == Suit.CLUBS


def _partner_bid_texas(ctx: BiddingContext) -> bool:
    """Partner bid 4D or 4H (Texas transfer)."""
    resp = _partner_bid(ctx)
    return resp.level == 4 and resp.suit in (Suit.DIAMONDS, Suit.HEARTS)


def _texas_suit(ctx: BiddingContext) -> Suit:
    """The suit partner Texas-transferred to (hearts if 4D, spades if 4H)."""
    resp = _partner_bid(ctx)
    if resp.suit == Suit.DIAMONDS:
        return Suit.HEARTS
    return Suit.SPADES


def _partner_bid_3_major(ctx: BiddingContext) -> bool:
    """Partner bid 3H or 3S (slam interest with 6+ card major)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit.is_major


def _partner_bid_2nt(ctx: BiddingContext) -> bool:
    """Partner bid 2NT (invitational)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit == Suit.NOTRUMP


def _partner_bid_3_minor(ctx: BiddingContext) -> bool:
    """Partner bid 3C or 3D (6+ minor, invitational)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit.is_minor


def _partner_bid_3nt(ctx: BiddingContext) -> bool:
    """Partner bid 3NT (to play)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit == Suit.NOTRUMP


def _partner_bid_4nt(ctx: BiddingContext) -> bool:
    """Partner bid 4NT (quantitative slam invite)."""
    resp = _partner_bid(ctx)
    return resp.level == 4 and resp.suit == Suit.NOTRUMP


def _ace_count(ctx: BiddingContext) -> int:
    """Count aces in opener's hand (for Gerber response)."""
    return sum(ctx.hand.has_card(s, Rank.ACE) for s in SUITS_SHDC)


# -- After Stayman (2C) -----------------------------------------------------


class RebidStayman2H(Rule):
    """2H -- 4+ hearts in response to Stayman.

    e.g. 1NT->2C->2H

    Bid hearts first with both 4-card majors (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_2h"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 575

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_stayman(ctx):
            return False
        return ctx.hand.num_hearts >= 4

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.HEARTS),
            rule_name=self.name,
            explanation="4+ hearts -- Stayman response over 1NT",
        )


class RebidStayman2S(Rule):
    """2S -- 4+ spades, no 4-card heart suit.

    e.g. 1NT->2C->2S

    Only bid spades when we don't have 4 hearts (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_2s"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 570

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_stayman(ctx):
            return False
        return ctx.hand.num_spades >= 4 and ctx.hand.num_hearts < 4

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.SPADES),
            rule_name=self.name,
            explanation="4+ spades, no 4-card heart suit -- Stayman response over 1NT",
        )


class RebidStayman2D(Rule):
    """2D -- no 4-card major.

    e.g. 1NT->2C->2D

    Denies both 4+ hearts and 4+ spades (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_2d"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 565

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_stayman(ctx):
            return False
        return ctx.hand.num_hearts < 4 and ctx.hand.num_spades < 4

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.DIAMONDS),
            rule_name=self.name,
            explanation="No 4-card major -- Stayman 2D denial over 1NT",
        )


# -- After Jacoby Transfer (2D/2H) ------------------------------------------


class RebidSuperAccept(Rule):
    """Super-accept -- jump to 3H/3S.

    e.g. 1NT->2D->3H, 1NT->2H->3S

    17 HCP maximum with 4+ card support for transfer suit.
    SAYC (research/05-conventions.md line 96).
    """

    @property
    def name(self) -> str:
        return "rebid.super_accept"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 560

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_transferred(ctx):
            return False
        suit = _transfer_suit(ctx)
        return ctx.hcp == 17 and ctx.hand.suit_length(suit) >= 4

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"17 HCP, 4+ {suit.letter} -- super-accept transfer over 1NT",
            alerts=(f"Super-accept -- 17 HCP with 4+ {suit.letter}",),
        )


class RebidCompleteTransfer(Rule):
    """Complete Jacoby transfer at cheapest level.

    e.g. 1NT->2D->2H, 1NT->2H->2S

    Default action (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.complete_transfer"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 555

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_transferred(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=f"Complete Jacoby transfer to 2{suit.letter} over 1NT",
        )


# -- After 2S Puppet --------------------------------------------------------


class RebidComplete2SPuppet(Rule):
    """3C -- forced response to 2S puppet.

    e.g. 1NT->2S->3C

    Opener must bid 3C; responder passes (clubs) or corrects to 3D.
    SAYC (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.complete_2s_puppet"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 552

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_2s_puppet(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.CLUBS),
            rule_name=self.name,
            explanation="Forced 3C response to 2S puppet over 1NT",
            alerts=("Forced relay -- responder will pass or correct to 3D",),
        )


# -- After Gerber (4C) ------------------------------------------------------


class RebidGerberResponse(Rule):
    """Gerber ace response -- 4D/4H/4S/4NT by ace count.

    e.g. 1NT->4C->4D (0/4 aces), 1NT->4C->4S (2 aces)

    0/4 aces = 4D, 1 = 4H, 2 = 4S, 3 = 4NT (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.gerber_response"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 550

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_gerber(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        aces = _ace_count(ctx)
        # 0/4 -> 4D, 1 -> 4H, 2 -> 4S, 3 -> 4NT
        response_map = {
            0: (Suit.DIAMONDS, "0 or 4"),
            1: (Suit.HEARTS, "1"),
            2: (Suit.SPADES, "2"),
            3: (Suit.NOTRUMP, "3"),
            4: (Suit.DIAMONDS, "0 or 4"),
        }
        suit, desc = response_map[aces]
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"{desc} aces -- Gerber response over 1NT",
            alerts=(f"Gerber response -- showing {desc} aces",),
        )


# -- After Texas Transfer (4D/4H) -------------------------------------------


class RebidCompleteTexas(Rule):
    """Complete Texas transfer -- 4H or 4S.

    e.g. 1NT->4D->4H, 1NT->4H->4S

    Opener always completes (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.complete_texas"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 545

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_texas(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _texas_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Complete Texas transfer to 4{suit.letter} over 1NT",
        )


# -- After 3H/3S (slam interest) --------------------------------------------


class RebidRaise3MajorOver1NT(Rule):
    """Raise 3M to 4M -- 3+ support, maximum.

    e.g. 1NT->3H->4H, 1NT->3S->4S

    16-17 HCP with 3+ cards in partner's major (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.raise_3_major_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 540

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_3_major(ctx):
            return False
        resp = _partner_bid(ctx)
        return ctx.hcp >= 16 and ctx.hand.suit_length(resp.suit) >= 3

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _partner_bid(ctx).suit
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"16-17 HCP, 3+ {suit.letter} -- raise to 4{suit.letter} over 1NT"
            ),
        )


class RebidDecline3MajorOver1NT(Rule):
    """Decline 3M -- bid 3NT.

    e.g. 1NT->3H->3NT, 1NT->3S->3NT

    Minimum (15 HCP) or fewer than 3 cards in partner's major.
    """

    @property
    def name(self) -> str:
        return "rebid.decline_3_major_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 535

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_3_major(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Minimum or short support -- decline 3M, bid 3NT over 1NT",
        )


# -- After 2NT (invite) -----------------------------------------------------


class RebidAccept2NTOver1NT(Rule):
    """Accept 2NT -- bid 3NT with maximum.

    e.g. 1NT->2NT->3NT

    16-17 HCP (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.accept_2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 530

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_2nt(ctx):
            return False
        return ctx.hcp >= 16

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16-17 HCP -- accept 2NT invite, bid 3NT over 1NT",
        )


class RebidDecline2NTOver1NT(Rule):
    """Decline 2NT -- pass with minimum.

    e.g. 1NT->2NT->Pass

    15 HCP (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.decline_2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 525

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_2nt(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="15 HCP -- decline 2NT invite, pass over 1NT",
        )


# -- After 3C/3D (minor invite) ---------------------------------------------


class RebidAccept3MinorOver1NT(Rule):
    """Accept 3m -- bid 3NT with maximum.

    e.g. 1NT->3C->3NT, 1NT->3D->3NT

    16-17 HCP (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.accept_3_minor_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 520

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_3_minor(ctx):
            return False
        return ctx.hcp >= 16

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16-17 HCP -- accept 3m invite, bid 3NT over 1NT",
        )


class RebidDecline3MinorOver1NT(Rule):
    """Decline 3m -- pass with minimum.

    e.g. 1NT->3C->Pass, 1NT->3D->Pass

    15 HCP (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.decline_3_minor_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 515

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_3_minor(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="15 HCP -- decline 3m invite, pass over 1NT",
        )


# -- After 3NT ---------------------------------------------------------------


class RebidPassAfter3NTOver1NT(Rule):
    """Pass -- 3NT is to play.

    e.g. 1NT->3NT->Pass

    Always pass (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_3nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 510

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_3nt(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="3NT to play -- pass over 1NT",
        )


# -- After 4NT (quantitative) ------------------------------------------------


class RebidAccept4NTOver1NT(Rule):
    """Accept 4NT -- bid 6NT with maximum.

    e.g. 1NT->4NT->6NT

    16-17 HCP (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.accept_4nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 505

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        if not _partner_bid_4nt(ctx):
            return False
        return ctx.hcp >= 16

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(6, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="16-17 HCP -- accept quantitative 4NT, bid 6NT",
        )


class RebidDecline4NTOver1NT(Rule):
    """Decline 4NT -- pass with minimum.

    e.g. 1NT->4NT->Pass

    15 HCP (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.decline_4nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 500

    def applies(self, ctx: BiddingContext) -> bool:
        if not _opened_1nt_self(ctx):
            return False
        return _partner_bid_4nt(ctx)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="15 HCP -- decline quantitative 4NT, pass",
        )
