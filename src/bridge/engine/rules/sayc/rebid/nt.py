"""Opener's rebid rules after 1NT and 2NT openings -- SAYC.

All rebid rules for when I opened 1NT (15-17 HCP balanced) or 2NT
(20-21 HCP balanced) and partner has responded. Covers:
- Stayman responses
- Jacoby transfer completion (normal + super-accept over 1NT)
- Puppet completion (2S->3C over 1NT, 3S->4C over 2NT)
- Gerber ace response (4D/4H/4S/4NT)
- Texas transfer completion (4H/4S)
- Raises/declines for 3M, 2NT, 3m, 3NT, 4NT

All rules belong to Category.REBID_OPENER.
"""

from bridge.engine.condition import (
    All,
    Condition,
    HasSuitFit,
    HcpRange,
    SuitLength,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid, is_suit_bid
from bridge.model.card import SUITS_SHDC, Rank, Suit

# -- Helpers -----------------------------------------------------------------


@condition("I opened 1NT")
def _i_opened_1nt(ctx: BiddingContext) -> bool:
    """Whether I opened 1NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 1 and bid.is_notrump


def _partner_bid(ctx: BiddingContext) -> SuitBid:
    """Partner's response (always a SuitBid in rebid phase after 1NT)."""
    resp = ctx.partner_last_bid
    assert resp is not None and is_suit_bid(resp)
    return resp


@condition("partner bid Stayman")
def _partner_bid_stayman(ctx: BiddingContext) -> bool:
    """Partner bid 2C (Stayman)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit == Suit.CLUBS


@condition("partner transferred")
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


@condition("partner bid 2S puppet")
def _partner_bid_2s_puppet(ctx: BiddingContext) -> bool:
    """Partner bid 2S (puppet to 3C)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.suit == Suit.SPADES


@condition("partner bid Gerber")
def _partner_bid_gerber(ctx: BiddingContext) -> bool:
    """Partner bid 4C (Gerber)."""
    resp = _partner_bid(ctx)
    return resp.level == 4 and resp.suit == Suit.CLUBS


@condition("partner bid Texas")
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


@condition("partner bid 3M")
def _partner_bid_3_major(ctx: BiddingContext) -> bool:
    """Partner bid 3H or 3S (slam interest with 6+ card major)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit.is_major


@condition("partner bid 2NT")
def _partner_bid_2nt(ctx: BiddingContext) -> bool:
    """Partner bid 2NT (invitational)."""
    resp = _partner_bid(ctx)
    return resp.level == 2 and resp.is_notrump


@condition("partner bid 3m")
def _partner_bid_3_minor(ctx: BiddingContext) -> bool:
    """Partner bid 3C or 3D (6+ minor, invitational)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit.is_minor


@condition("partner bid 3NT")
def _partner_bid_3nt(ctx: BiddingContext) -> bool:
    """Partner bid 3NT (to play)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.is_notrump


@condition("partner bid 4NT")
def _partner_bid_4nt(ctx: BiddingContext) -> bool:
    """Partner bid 4NT (quantitative slam invite)."""
    resp = _partner_bid(ctx)
    return resp.level == 4 and resp.is_notrump


def _ace_count(ctx: BiddingContext) -> int:
    """Count aces in opener's hand (for Gerber response)."""
    return sum(ctx.hand.has_card(s, Rank.ACE) for s in SUITS_SHDC)


# -- 2NT helpers -------------------------------------------------------------


@condition("I opened 2NT")
def _i_opened_2nt(ctx: BiddingContext) -> bool:
    """Whether I opened 2NT."""
    if not ctx.my_bids:
        return False
    bid = ctx.my_bids[0]
    return is_suit_bid(bid) and bid.level == 2 and bid.is_notrump


@condition("partner bid Stayman over 2NT")
def _partner_bid_stayman_2nt(ctx: BiddingContext) -> bool:
    """Partner bid 3C (Stayman over 2NT)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit == Suit.CLUBS


@condition("partner transferred over 2NT")
def _partner_transferred_2nt(ctx: BiddingContext) -> bool:
    """Partner bid 3D (hearts) or 3H (spades) -- transfer over 2NT."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit in (Suit.DIAMONDS, Suit.HEARTS)


def _transfer_suit_2nt(ctx: BiddingContext) -> Suit:
    """The suit partner transferred to over 2NT (hearts if 3D, spades if 3H)."""
    resp = _partner_bid(ctx)
    if resp.suit == Suit.DIAMONDS:
        return Suit.HEARTS
    return Suit.SPADES


@condition("partner bid 3S puppet")
def _partner_bid_3s_puppet(ctx: BiddingContext) -> bool:
    """Partner bid 3S (puppet to 4C over 2NT)."""
    resp = _partner_bid(ctx)
    return resp.level == 3 and resp.suit == Suit.SPADES


def _partner_bid_suit(ctx: BiddingContext) -> Suit:
    """Partner's response suit (for HasSuitFit)."""
    return _partner_bid(ctx).suit


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

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1nt, _partner_bid_stayman, SuitLength(Suit.HEARTS, min_len=4)
        )

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

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1nt,
            _partner_bid_stayman,
            SuitLength(Suit.SPADES, min_len=4),
            SuitLength(Suit.HEARTS, max_len=3),
        )

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

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1nt,
            _partner_bid_stayman,
            SuitLength(Suit.HEARTS, max_len=3),
            SuitLength(Suit.SPADES, max_len=3),
        )

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

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1nt,
            _partner_transferred,
            HcpRange(17, 17),
            HasSuitFit(_transfer_suit, min_len=4),
        )

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_transferred)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_2s_puppet)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_gerber)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_texas)

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

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_1nt,
            _partner_bid_3_major,
            HcpRange(min_hcp=16),
            HasSuitFit(_partner_bid_suit, min_len=3),
        )

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_3_major)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_2nt, HcpRange(min_hcp=16))

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_2nt)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_3_minor, HcpRange(min_hcp=16))

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_3_minor)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_3nt)

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_4nt, HcpRange(min_hcp=16))

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

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_1nt, _partner_bid_4nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="15 HCP -- decline quantitative 4NT, pass",
        )


# ══════════════════════════════════════════════════════════════════════
# Opener's rebids after 2NT opening (20-21 HCP balanced)
# ══════════════════════════════════════════════════════════════════════


# -- After Stayman (3C) over 2NT -------------------------------------------


class Rebid2NTStayman3H(Rule):
    """3H -- 4+ hearts in response to Stayman over 2NT.

    e.g. 2NT->3C->3H

    Bid hearts first with both 4-card majors (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_3h_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 574

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2nt,
            _partner_bid_stayman_2nt,
            SuitLength(Suit.HEARTS, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.HEARTS),
            rule_name=self.name,
            explanation="4+ hearts -- Stayman response over 2NT",
        )


class Rebid2NTStayman3S(Rule):
    """3S -- 4+ spades, no 4-card heart suit over 2NT.

    e.g. 2NT->3C->3S

    Only bid spades when we don't have 4 hearts (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_3s_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 569

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2nt,
            _partner_bid_stayman_2nt,
            SuitLength(Suit.SPADES, min_len=4),
            SuitLength(Suit.HEARTS, max_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.SPADES),
            rule_name=self.name,
            explanation="4+ spades, no 4-card heart suit -- Stayman response over 2NT",
        )


class Rebid2NTStayman3D(Rule):
    """3D -- no 4-card major over 2NT.

    e.g. 2NT->3C->3D

    Denies both 4+ hearts and 4+ spades (research/05-conventions.md).
    """

    @property
    def name(self) -> str:
        return "rebid.stayman_3d_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 564

    @property
    def conditions(self) -> Condition:
        return All(
            _i_opened_2nt,
            _partner_bid_stayman_2nt,
            SuitLength(Suit.HEARTS, max_len=3),
            SuitLength(Suit.SPADES, max_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.DIAMONDS),
            rule_name=self.name,
            explanation="No 4-card major -- Stayman 3D denial over 2NT",
        )


# -- After Transfer (3D/3H) over 2NT ---------------------------------------


class Rebid2NTCompleteTransfer(Rule):
    """Complete Jacoby transfer over 2NT.

    e.g. 2NT->3D->3H, 2NT->3H->3S

    Always complete at cheapest level. No super-accept over 2NT
    (already at max range).
    """

    @property
    def name(self) -> str:
        return "rebid.complete_transfer_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 554

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_transferred_2nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _transfer_suit_2nt(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"Complete Jacoby transfer to 3{suit.letter} over 2NT",
        )


# -- After 3S Puppet over 2NT ----------------------------------------------


class Rebid2NTComplete3SPuppet(Rule):
    """4C -- forced response to 3S puppet over 2NT.

    e.g. 2NT->3S->4C

    Opener must bid 4C; responder passes (clubs) or corrects to 4D.
    """

    @property
    def name(self) -> str:
        return "rebid.complete_3s_puppet_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 551

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_3s_puppet)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.CLUBS),
            rule_name=self.name,
            explanation="Forced 4C response to 3S puppet over 2NT",
            alerts=("Forced relay -- responder will pass or correct to 4D",),
        )


# -- After Gerber (4C) over 2NT --------------------------------------------


class Rebid2NTGerberResponse(Rule):
    """Gerber ace response over 2NT -- 4D/4H/4S/4NT by ace count.

    e.g. 2NT->4C->4D (0/4 aces), 2NT->4C->4S (2 aces)

    0/4 aces = 4D, 1 = 4H, 2 = 4S, 3 = 4NT (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.gerber_response_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 549

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_gerber)

    def select(self, ctx: BiddingContext) -> RuleResult:
        aces = _ace_count(ctx)
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
            explanation=f"{desc} aces -- Gerber response over 2NT",
            alerts=(f"Gerber response -- showing {desc} aces",),
        )


# -- After Texas Transfer (4D/4H) over 2NT ---------------------------------


class Rebid2NTCompleteTexas(Rule):
    """Complete Texas transfer over 2NT -- 4H or 4S.

    e.g. 2NT->4D->4H, 2NT->4H->4S

    Opener always completes (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.complete_texas_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 544

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_texas)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _texas_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"Complete Texas transfer to 4{suit.letter} over 2NT",
        )


# -- After 3NT over 2NT ----------------------------------------------------


class Rebid2NTPassAfter3NT(Rule):
    """Pass -- 3NT is to play over 2NT.

    e.g. 2NT->3NT->Pass

    Always pass (research/02-responses.md).
    """

    @property
    def name(self) -> str:
        return "rebid.pass_after_3nt_over_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 509

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_3nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="3NT to play -- pass over 2NT",
        )


# -- After 4NT (quantitative) over 2NT -------------------------------------


class Rebid2NTAccept4NT(Rule):
    """Accept 4NT -- bid 6NT with maximum over 2NT.

    e.g. 2NT->4NT->6NT

    21 HCP (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.accept_4nt_over_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 504

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_4nt, HcpRange(min_hcp=21))

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(6, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="21 HCP -- accept quantitative 4NT, bid 6NT over 2NT",
        )


class Rebid2NTDecline4NT(Rule):
    """Decline 4NT -- pass with minimum over 2NT.

    e.g. 2NT->4NT->Pass

    20 HCP (research/06-slam.md).
    """

    @property
    def name(self) -> str:
        return "rebid.decline_4nt_over_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_OPENER

    @property
    def priority(self) -> int:
        return 499

    @property
    def conditions(self) -> Condition:
        return All(_i_opened_2nt, _partner_bid_4nt)

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="20 HCP -- decline quantitative 4NT, pass over 2NT",
        )
