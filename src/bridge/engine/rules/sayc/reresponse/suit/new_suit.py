"""Section F: After I Bid a New Suit at 1-Level (1x->1y->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import (
    All,
    Balanced,
    Computed,
    Condition,
    HasSuitFit,
    HcpRange,
    SuitFinderComputed,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    find_fourth_suit_bid,
    find_new_suit_forcing,
    i_responded_in_a_major,
    i_responded_in_a_minor,
    my_response,
    my_response_suit,
    my_response_suit_5,
    my_response_suit_5plus,
    my_response_suit_6plus,
    opening_bid,
    opening_is_major,
    opening_suit,
    partner_jump_rebid_own_suit,
    partner_jump_shifted,
    partner_opened_1_suit,
    partner_raised_my_suit,
    partner_rebid,
    partner_rebid_2nt,
    partner_rebid_3nt,
    partner_rebid_new_suit,
    partner_rebid_own_suit,
    partner_rebid_suit,
    stoppers_in_unbid,
)

__all__ = [
    "Accept3yJumpRaise",
    "Accept3yJumpRaise3NT",
    "Decline3yJumpRaise",
    "FourMAfter1NTRebid",
    "FourMAfter2NTRebid",
    "FourMAfterJumpRebid",
    "FourMAfterNewSuit",
    "FourMAfterOwnSuitMajor",
    "FourMAfterRaise",
    "FourthSuitAfterOwnSuit",
    "FourthSuitForcing",
    "GFAfterReverse",
    "GFRaiseReverseSuit",
    "JumpInOwnSuitAfterReverse",
    "JumpOwnMajorAfter1NT",
    "JumpRebidOwnSuitAfterNewSuit",
    "JumpRebidOwnSuitAfterOwnSuit",
    "JumpRebidAfter1NT",
    "NewSuitAfter1NTForcing",
    "NewSuitAt1Level",
    "NewSuitForcingAfterMinorRaise",
    "NewSuitForcingAfterOwnSuit",
    "NewSuitWeakAfter1NT",
    "OneNTReresponse",
    "PassAfter1NTRebid",
    "PassAfter2NTRebid",
    "PassAfter3NTRebid",
    "PassAfterDoubleJumpRaise",
    "PassAfterDoubleJumpRebid",
    "PassAfterJumpRebid",
    "PassAfterNewSuit",
    "PassAfterRaise",
    "PreferenceAfterOwnSuit",
    "PreferenceAfterReverse",
    "PreferenceToOpenerFirst",
    "RaiseJumpShiftSuit",
    "RaiseNewSuitInvite",
    "RaiseReverseSuit",
    "RebidOwnSuitAfter1NT",
    "RebidOwnSuitAfterJS",
    "RebidOwnSuitAfterNewSuit",
    "RebidOwnSuitAfterOwnSuit",
    "RebidOwnSuitAfterReverse",
    "SupportOpenerFirstAfterJS",
    "ThreeNTAfter1NTRebid",
    "ThreeNTAfter2NTRebid",
    "ThreeNTAfterJumpRebid",
    "ThreeNTAfterJumpRebidNoStoppers",
    "ThreeNTAfterJumpShift",
    "ThreeNTAfterNewSuit",
    "ThreeNTAfterOwnSuit",
    "ThreeNTAfterRaise",
    "ThreeNTAfterReverse",
    "ThreeSuitAfter2NTRebid",
    "ThreeXInviteAfterOwnSuit",
    "ThreeYInviteAfterRaise",
    "TwoNTAfter1NTRebid",
    "TwoNTAfterNewSuit",
    "TwoNTAfterOwnSuit",
    "TwoNTAfterReverse",
    "WeakRaiseNewSuit",
]


# ── Section F helpers ─────────────────────────────────


@condition("I bid a new suit at the 1-level")
def _i_bid_new_suit_1level(ctx: BiddingContext) -> bool:
    """I bid a new suit at the 1-level (e.g. 1D->1S)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    return resp.level == 1 and not resp.is_notrump and resp.suit != opening.suit


@condition("partner reversed")
def _partner_reversed(ctx: BiddingContext) -> bool:
    """Partner made a reverse bid (higher new suit at cheapest level, 17+ HCP)."""
    opening = opening_bid(ctx)
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    if rebid.is_notrump or rebid.suit == opening.suit:
        return False
    if not my_resp.is_notrump and rebid.suit == my_resp.suit:
        return False
    # Reverse: new suit ranks above opener's first suit, at 2-level+, at cheapest level.
    # A 1-level bid (e.g. 1C->1D->1H) is NOT a reverse -- no extra values needed.
    # A jump in a higher-ranking suit is a jump shift, not a reverse.
    cheapest = cheapest_bid_in_suit(rebid.suit, my_resp)
    if cheapest is None:
        return False
    return (
        rebid.suit > opening.suit and rebid.level >= 2 and rebid.level == cheapest.level
    )


@condition("partner jump-raised my suit")
def _partner_jump_raised_my_suit(ctx: BiddingContext) -> bool:
    """Partner jump-raised my response suit."""
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    if my_resp.is_notrump:
        return False
    cheapest = cheapest_bid_in_suit(my_resp.suit, my_resp)
    if cheapest is None:
        return False
    return rebid.suit == my_resp.suit and rebid.level == cheapest.level + 1


@condition("partner double-jump-raised my suit")
def _partner_double_jump_raised(ctx: BiddingContext) -> bool:
    """Partner double-jump-raised my suit (to 4-level)."""
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    if my_resp.is_notrump:
        return False
    cheapest = cheapest_bid_in_suit(my_resp.suit, my_resp)
    if cheapest is None:
        return False
    return rebid.suit == my_resp.suit and rebid.level == cheapest.level + 2


@condition("partner rebid 1NT")
def _partner_rebid_1nt(ctx: BiddingContext) -> bool:
    rebid = partner_rebid(ctx)
    return rebid.is_notrump and rebid.level == 1


@condition("partner double-jump-rebid own suit")
def _partner_double_jump_rebid_own_suit(ctx: BiddingContext) -> bool:
    """Partner double-jump-rebid their opening suit (e.g. 1H->1S->4H)."""
    opening = opening_bid(ctx)
    my_resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    if rebid.suit != opening.suit:
        return False
    cheapest = cheapest_bid_in_suit(opening.suit, my_resp)
    if cheapest is None:
        return False
    return rebid.level == cheapest.level + 2


@condition("partner rebid new suit at 1-level")
def _partner_rebid_new_suit_1_level(ctx: BiddingContext) -> bool:
    """Partner rebid a new suit at the 1-level (e.g. 1C->1D->1H)."""
    return partner_rebid_new_suit(ctx) and partner_rebid(ctx).level == 1


def _find_new_suit_at_1_level(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card suit biddable at the 1-level above partner's rebid.

    Only possible after 1C->1D->1H (bid 1S). Returns None otherwise.
    """
    rebid = partner_rebid(ctx)
    if rebid.level != 1:
        return None
    exclude = {opening_suit(ctx), my_response_suit(ctx), rebid.suit}
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit in exclude:
            continue
        if suit > rebid.suit and ctx.hand.suit_length(suit) >= 4:
            return suit
    return None


def _find_new_suit_lower(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card new suit lower-ranking than my response suit.

    For weak sign-offs after 1NT rebid (non-forcing).
    """
    my_suit = my_response_suit(ctx)
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit >= my_suit or suit == opening_suit(ctx):
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 4 and length > best_len:
            best = suit
            best_len = length
    return best


def _find_new_suit_forcing_after_1nt(ctx: BiddingContext) -> Suit | None:
    """Find a 4+ card new suit higher than response suit.

    After 1x->1y->1NT, a 2-level bid below y is weak by convention.
    Only consider suits that rank at or above the response suit so the
    bid is unambiguously forcing.
    """
    opening = opening_suit(ctx)
    my_suit = my_response_suit(ctx)
    best: Suit | None = None
    best_len = 0
    for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
        if suit == opening or suit <= my_suit:
            continue
        length = ctx.hand.suit_length(suit)
        if length >= 4 and length > best_len:
            best = suit
            best_len = length
    return best


# ── F1: After Opener Rebid 1NT (1x->1y->1NT->?) ─────────────────


class ThreeNTAfter1NTRebid(Rule):
    """Bid 3NT -- game-forcing with balanced hand.

    1x->1y->1NT->3NT. 13-15 HCP, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_1nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 356

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13, max_hcp=15), Balanced(strict=True))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13-15 HCP balanced after 1NT rebid -- 3NT",
        )


class FourMAfter1NTRebid(Rule):
    """Bid game in own major with 6+ cards.

    1x->1y->1NT->4M. 13+ HCP, 6+ card major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_1nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 367

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_rebid_1nt,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13+ HCP, 6+ card major after 1NT -- game in 4{suit.letter}",
        )


class JumpOwnMajorAfter1NT(Rule):
    """Jump rebid own major -- game forcing, 5+ cards.

    1x->1y->1NT->3M. 13+ HCP, 5+ card major (not 6).
    Asks opener to choose between 3NT and 4M.
    """

    @property
    def name(self) -> str:
        return "reresponse.jump_own_major_after_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 349

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_rebid_1nt,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), my_response_suit_5)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"13+ HCP, 5 card major after 1NT -- GF 3{suit.letter}",
            forcing=True,
        )


class NewSuitAfter1NTForcing(Rule):
    """Bid a new suit -- game forcing.

    1x->1y->1NT->new suit. 13+ HCP, 4+ card new suit.
    """

    def __init__(self) -> None:
        self._new_suit = SuitFinderComputed(
            _find_new_suit_forcing_after_1nt,
            "4+ card higher new suit",
            min_len=4,
        )

    @property
    def name(self) -> str:
        return "reresponse.new_suit_after_1nt_forcing"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 347

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), self._new_suit)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        opening = opening_suit(ctx)
        my_suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bids = []
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit == opening or suit <= my_suit:
                continue
            bid = cheapest_bid_in_suit(suit, rebid)
            if bid is not None:
                bids.append(bid)
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"13+ HCP, new suit after 1NT -- forcing {bid}",
            forcing=True,
        )


class TwoNTAfter1NTRebid(Rule):
    """Bid 2NT -- invitational.

    1x->1y->1NT->2NT. 11-12 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_1nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 278

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=11, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="11-12 HCP after 1NT rebid -- invitational 2NT",
        )


class JumpRebidAfter1NT(Rule):
    """Jump rebid own suit -- invitational, 6+ cards.

    1x->1y->1NT->3y. 11-12 HCP, 6+ card suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.jump_rebid_after_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 288

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=11, max_hcp=12), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"11-12 HCP, 6+ cards after 1NT -- invitational 3{suit.letter}",
        )


class NewSuitWeakAfter1NT(Rule):
    """Bid a new suit -- weak, non-forcing.

    1x->1y->1NT->2z (lower than y). 6-10 HCP, 4+ cards.
    """

    def __init__(self) -> None:
        self._new_suit = SuitFinderComputed(
            _find_new_suit_lower,
            "4+ card lower new suit",
            min_len=4,
        )

    @property
    def name(self) -> str:
        return "reresponse.new_suit_weak_after_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 195

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), self._new_suit)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        my_suit = my_response_suit(ctx)
        opening = opening_suit(ctx)
        bids = []
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit >= my_suit or suit == opening:
                continue
            bids.append(SuitBid(2, suit))
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=f"6-10 HCP, 4+ {suit.letter} -- weak sign-off",
        )


class RebidOwnSuitAfter1NT(Rule):
    """Rebid own suit -- weak sign-off, 6+ cards.

    1x->1y->1NT->2y. 6-10 HCP, 6+ card suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 193

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(2, suit),
            rule_name=self.name,
            explanation=f"6-10 HCP, 6+ cards -- sign-off 2{suit.letter}",
        )


class PassAfter1NTRebid(Rule):
    """Pass after opener's 1NT rebid.

    1x->1y->1NT->Pass. 6-10 HCP, no long suit, no side suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_1nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 97

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_rebid_1nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=10)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-10 HCP, content with 1NT -- pass",
        )


# ── F2: After Opener Raised My Suit (1x->1y->2y->?) ─────────────


class FourMAfterRaise(Rule):
    """Bid game in major after raise.

    1x->1y->2y->4M. 13+ HCP, major suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 370

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_raised_my_suit,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=13)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13+ HCP, game in major after raise -- 4{suit.letter}",
        )


class ThreeNTAfterRaise(Rule):
    """Bid 3NT after raise of minor.

    1x->1y->2y->3NT. 13+ HCP, minor, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 360

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_raised_my_suit,
            i_responded_in_a_minor,
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=13))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13+ HCP, minor raised -- 3NT",
        )


class NewSuitForcingAfterMinorRaise(Rule):
    """Bid a new suit forcing after minor raise without stoppers.

    1x->1y->2y->new suit. 13+ HCP, minor raised, no stoppers.
    Bid longest unbid suit as a forcing new suit to explore.
    Only applies when response was a minor (major raises use FourMAfterRaise).
    """

    def __init__(self) -> None:
        self._new_suit = SuitFinderComputed(
            find_new_suit_forcing,
            "new suit forcing",
            min_len=4,
        )

    @property
    def name(self) -> str:
        return "reresponse.new_suit_forcing_after_minor_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 355

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_raised_my_suit,
            i_responded_in_a_minor,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), self._new_suit)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        exclude = {opening_suit(ctx), my_response_suit(ctx)}
        rebid = partner_rebid(ctx)
        bids = []
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit in exclude:
                continue
            bid = cheapest_bid_in_suit(suit, rebid)
            if bid is not None:
                bids.append(bid)
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"13+ HCP, minor raised, no stoppers -- {bid} forcing",
            forcing=True,
        )


class ThreeYInviteAfterRaise(Rule):
    """Invite game after raise.

    1x->1y->2y->3y. 11-12 HCP, invitational.
    """

    @property
    def name(self) -> str:
        return "reresponse.3y_invite_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 287

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_raised_my_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=11, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"11-12 HCP, invitational after raise -- 3{suit.letter}",
        )


class PassAfterRaise(Rule):
    """Pass after raise.

    1x->1y->2y->Pass. 6-10 HCP, content with partscore.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 98

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_raised_my_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=10)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-10 HCP after raise -- pass",
        )


# ── F3: After Opener Jump Raised My Suit (1x->1y->3y->?) ────────


class Accept3yJumpRaise(Rule):
    """Accept jump raise invitation -- game in major.

    1x->1y->3y->4M. 9+ HCP, major.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_3y_jump_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 342

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_jump_raised_my_suit,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=9)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"9+ HCP, accept jump raise -- 4{suit.letter}",
        )


class Accept3yJumpRaise3NT(Rule):
    """Accept jump raise invitation -- game in NT (minor).

    1x->1y->3y->3NT. 9+ HCP, minor.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_3y_jump_raise_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 338

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_jump_raised_my_suit,
            i_responded_in_a_minor,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=9), stoppers_in_unbid)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="9+ HCP, minor jump raised, stoppers -- 3NT",
        )


class Decline3yJumpRaise(Rule):
    """Decline jump raise invitation.

    1x->1y->3y->Pass. 6-8 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_3y_jump_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 188

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, _partner_jump_raised_my_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=8)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-8 HCP, decline jump raise -- pass",
        )


# ── F4: After Opener Double Jump Raised (1x->1y->4y->?) ─────────


class PassAfterDoubleJumpRaise(Rule):
    """Pass after double jump raise -- game reached.

    1x->1y->4y->Pass.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_double_jump_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 87

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, _partner_double_jump_raised
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after double jump raise -- pass",
        )


# ── F5: After Opener Rebid Own Suit (1x->1y->2x->?) ─────────────


class ThreeNTAfterOwnSuit(Rule):
    """Bid 3NT after opener rebid own suit.

    1x->1y->2x->3NT. 13+ HCP, balanced, stoppers.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 352

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=13), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13+ HCP, balanced, stoppers -- 3NT",
        )


class FourMAfterOwnSuitMajor(Rule):
    """Bid 4M after opener rebid own major suit.

    1x->1y->2x->4M. 13+ HCP, 3+ support, opening suit is major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_own_suit_major"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 366

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_rebid_own_suit,
            opening_is_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13+ HCP, 3+ support -- game in 4{suit.letter}",
        )


class FourthSuitAfterOwnSuit(Rule):
    """Fourth suit forcing after opener rebid own suit.

    1x->1y->2x->fourth suit. 13+ HCP, no clear bid.
    """

    def __init__(self) -> None:
        self._fsf = Computed(find_fourth_suit_bid, "fourth suit available")

    @property
    def name(self) -> str:
        return "reresponse.fourth_suit_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 350

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), self._fsf)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = find_fourth_suit_bid(ctx)
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        bid = self._fsf.value
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"13+ HCP, fourth suit forcing -- {bid}",
            forcing=True,
        )


class NewSuitForcingAfterOwnSuit(Rule):
    """Bid a new suit -- forcing, game-going.

    1x->1y->2x->new suit. 13+ HCP, 4+ cards in an unbid suit.
    Used when FSF is unavailable (only 2 suits bid, 2 unbid).
    A new suit by responder is forcing one round in SAYC.
    """

    def __init__(self) -> None:
        self._new_suit = SuitFinderComputed(
            find_new_suit_forcing,
            "new suit forcing",
            min_len=4,
        )

    @property
    def name(self) -> str:
        return "reresponse.new_suit_forcing_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 348

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), self._new_suit)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        exclude = {opening_suit(ctx), my_response_suit(ctx)}
        rebid = partner_rebid(ctx)
        bids = []
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit in exclude:
                continue
            bid = cheapest_bid_in_suit(suit, rebid)
            if bid is not None:
                bids.append(bid)
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"13+ HCP, 4+ {suit.letter} -- new suit forcing {bid}",
            forcing=True,
        )


class TwoNTAfterOwnSuit(Rule):
    """Bid 2NT after opener rebid own suit -- invitational.

    1x->1y->2x->2NT. 11-12 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 282

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=11, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="11-12 HCP after own suit rebid -- invitational 2NT",
        )


class JumpRebidOwnSuitAfterOwnSuit(Rule):
    """Jump rebid own suit -- invitational.

    1x->1y->2x->3y. 11-12 HCP, 6+ cards in response suit.
    More descriptive than 2NT when holding a long suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.jump_rebid_own_suit_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 284

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=11, max_hcp=12), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"11-12 HCP, 6+ {suit.letter} -- invitational 3{suit.letter}",
        )


class ThreeXInviteAfterOwnSuit(Rule):
    """Raise opener's suit invitational.

    1x->1y->2x->3x. 11-12 HCP, 3+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.3x_invite_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 281

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=11, max_hcp=12), HasSuitFit(opening_suit, min_len=3)
        )

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"11-12 HCP, 3+ support -- invitational 3{suit.letter}",
        )


class RebidOwnSuitAfterOwnSuit(Rule):
    """Rebid own suit -- preference, 6+ cards.

    1x->1y->2x->2y. 6-10 HCP, 6+ cards in own suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 192

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(my_response_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-10 HCP, 6+ cards -- preference for own suit {bid}",
        )


class PreferenceAfterOwnSuit(Rule):
    """Pass with tolerance for opener's suit.

    1x->1y->2x->Pass. 6-10 HCP, 2+ in opener's suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 99

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=10)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-10 HCP, content with opener's suit -- pass",
        )


# ── F6: After Opener Jump Rebid Own Suit (1x->1y->3x->?) ────────


class FourMAfterJumpRebid(Rule):
    """Accept jump rebid invitation -- game in major.

    1x->1y->3x->4M. 8+ HCP, 3+ support, major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_jump_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 340

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_jump_rebid_own_suit,
            opening_is_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"8+ HCP, 3+ support -- accept, game in 4{suit.letter}",
        )


class ThreeNTAfterJumpRebid(Rule):
    """Accept jump rebid invitation -- game in NT.

    1x->1y->3x->3NT. 8+ HCP, no major support.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_jump_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 337

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=8))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8+ HCP after jump rebid -- 3NT",
        )


class ThreeNTAfterJumpRebidNoStoppers(Rule):
    """Bid 3NT after opener jump rebid -- no stoppers but game values.

    1x->1y->3x->3NT. 8+ HCP, without stoppers in unbid suits.
    With enough combined values for game, accept the risk.
    Lower priority than stopper-checked version.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_jump_rebid_no_stoppers"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 335

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=8)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8+ HCP after jump rebid -- 3NT (no stopper check)",
        )


class PassAfterJumpRebid(Rule):
    """Decline jump rebid invitation.

    1x->1y->3x->Pass. 6-7 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_jump_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 184

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_rebid_own_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=7)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-7 HCP, decline jump rebid -- pass",
        )


# ── F7: After Opener Bid New Suit Non-Reverse (1x->1y->2z->?) ───


class FourMAfterNewSuit(Rule):
    """Bid game in own major after opener's new suit.

    1x->1y->2z->4M. 13+ HCP, 5+ own suit, major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 371

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_rebid_new_suit,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), my_response_suit_5plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"13+ HCP, 5+ card major -- game in 4{suit.letter}",
        )


class ThreeNTAfterNewSuit(Rule):
    """Bid 3NT after opener's new suit.

    1x->1y->2z->3NT. 13+ HCP, balanced, stoppers.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 361

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=13), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13+ HCP, balanced -- 3NT",
        )


class FourthSuitForcing(Rule):
    """Fourth suit forcing after opener's new suit.

    1x->1y->2z->fourth suit. 13+ HCP.
    """

    def __init__(self) -> None:
        self._fsf = Computed(find_fourth_suit_bid, "fourth suit available")

    @property
    def name(self) -> str:
        return "reresponse.fourth_suit_forcing"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 357

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), self._fsf)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = find_fourth_suit_bid(ctx)
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        bid = self._fsf.value
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"13+ HCP, fourth suit forcing -- {bid}",
            forcing=True,
        )


class RaiseNewSuitInvite(Rule):
    """Raise opener's new suit -- invitational (after 2-level rebid).

    1x->1y->2z->3z. 11-12 HCP, 4+ support for z.
    After a 2-level rebid, cheapest raise IS the jump (invitational).
    For 1-level rebids, see InviteJumpRaiseNewSuit.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_new_suit_invite"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 292

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=11, max_hcp=12), HasSuitFit(partner_rebid_suit, min_len=4)
        )

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        if bid is None:
            return frozenset()
        if rebid.level == 1:
            bid = SuitBid(bid.level + 1, suit)
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        # After 1-level rebid, jump one level for invitational
        if rebid.level == 1:
            bid = SuitBid(bid.level + 1, suit)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"11-12 HCP, 4+ {suit.letter} -- invitational raise {bid}",
        )


class JumpRebidOwnSuitAfterNewSuit(Rule):
    """Jump rebid own suit after opener's new suit -- invitational.

    1x->1y->2z->3y. 11-12 HCP, 6+ cards in response suit.
    More descriptive than 2NT when holding a long suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.jump_rebid_own_suit_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 289

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=11, max_hcp=12), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"11-12 HCP, 6+ {suit.letter} -- invitational 3{suit.letter}",
        )


class TwoNTAfterNewSuit(Rule):
    """Bid 2NT after opener's new suit -- invitational.

    1x->1y->2z->2NT. 11-12 HCP, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 283

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=11, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="11-12 HCP after new suit -- invitational 2NT",
        )


class PreferenceToOpenerFirst(Rule):
    """Give preference to opener's first suit.

    1x->1y->2z->2x. 6-10 HCP, 3+ in opener's first suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_to_opener_first"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 196

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(opening_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-10 HCP, 3+ {suit.letter} -- preference to first suit {bid}",
        )


class RebidOwnSuitAfterNewSuit(Rule):
    """Rebid own suit after opener's new suit.

    1x->1y->2z->2y. 6-10 HCP, 6+ cards.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 194

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(my_response_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-10 HCP, 6+ cards -- rebid own suit {bid}",
        )


class PassAfterNewSuit(Rule):
    """Pass with tolerance for opener's new suit.

    1x->1y->2z->Pass. 6-10 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 96

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_new_suit
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=10)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-10 HCP, tolerance for opener's new suit -- pass",
        )


# ── F7b: Extra rules for 1-level new suit rebids (1x->1y->1z->?) ──


class NewSuitAt1Level(Rule):
    """Bid a new suit at the 1-level -- natural, forcing.

    1C->1D->1H->1S. 6+ HCP, 4+ cards in a suit biddable at 1-level.
    Only possible after 1C->1D->1H (bidding 1S).
    """

    @property
    def name(self) -> str:
        return "reresponse.new_suit_at_1_level"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 262

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_rebid_new_suit_1_level,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=6),
            SuitFinderComputed(
                _find_new_suit_at_1_level,
                "new suit at 1-level",
                min_len=4,
            ),
        )

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        exclude = {opening_suit(ctx), my_response_suit(ctx), partner_rebid_suit(ctx)}
        rebid = partner_rebid(ctx)
        bids = []
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit in exclude or suit <= rebid.suit:
                continue
            bids.append(SuitBid(1, suit))
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = _find_new_suit_at_1_level(ctx)
        assert suit is not None
        return RuleResult(
            bid=SuitBid(1, suit),
            rule_name=self.name,
            explanation=f"6+ HCP, 4+ {suit.letter} -- natural 1{suit.letter}, forcing",
            forcing=True,
        )


class WeakRaiseNewSuit(Rule):
    """Raise opener's new suit -- weak (after 1-level rebid).

    1x->1y->1z->2z. 6-10 HCP, 4+ support for z.
    """

    @property
    def name(self) -> str:
        return "reresponse.weak_raise_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 200

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_rebid_new_suit_1_level,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), HasSuitFit(partner_rebid_suit, min_len=4))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(partner_rebid_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-10 HCP, 4+ {suit.letter} -- simple raise {bid}",
        )


class OneNTReresponse(Rule):
    """Bid 1NT -- weak, balanced, no fit (after 1-level rebid).

    1x->1y->1z->1NT. 6-10 HCP, balanced, no support for opener's suits.
    """

    @property
    def name(self) -> str:
        return "reresponse.1nt_reresponse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 100

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_rebid_new_suit_1_level,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=10), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(1, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(1, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="6-10 HCP, balanced -- 1NT sign-off",
        )


# ── F8: After Opener Reversed (1x->1y->2z reverse->?) ───────────


class ThreeNTAfterReverse(Rule):
    """Bid 3NT after opener reversed.

    1x->1y->2z(rev)->3NT. 13+ HCP, balanced, stoppers.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 368

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=13), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13+ HCP, balanced after reverse -- 3NT",
        )


class GFRaiseReverseSuit(Rule):
    """Raise reverse suit -- game forcing.

    1x->1y->2z(rev)->4z/3NT. 13+ HCP, 4+ in reverse suit.
    With opener's 17+ (reverse) + responder's 13+ = 30+ combined.
    Major fit: bid game (4z). Minor fit: bid 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.gf_raise_reverse_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 372

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=13), HasSuitFit(partner_rebid_suit, min_len=4))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        suit = partner_rebid_suit(ctx)
        if suit.is_major:
            return frozenset({SuitBid(4, suit)})
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        if suit.is_major:
            bid = SuitBid(4, suit)
            return RuleResult(
                bid=bid,
                rule_name=self.name,
                explanation=f"13+ HCP, 4+ {suit.letter} after reverse -- game {bid}",
            )
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=f"13+ HCP, 4+ {suit.letter} (minor) after reverse -- 3NT",
        )


class RaiseReverseSuit(Rule):
    """Raise the reverse suit -- invitational.

    1x->1y->2z(rev)->3z. 10-12 HCP, 4+ in reverse suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_reverse_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 297

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=10, max_hcp=12), HasSuitFit(partner_rebid_suit, min_len=4)
        )

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(partner_rebid_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=(
                f"10-12 HCP, 4+ {suit.letter} --"
                f" invitational raise of reverse suit {bid}"
            ),
        )


class GFAfterReverse(Rule):
    """Game-forcing action after reverse -- new suit or 3NT.

    1x->1y->2z(rev)->?. 13+ HCP, no 4+ fit in reverse suit.
    With opener's 17+ (reverse) + responder's 13+ = 30+ combined.
    Bid a 4+ card unbid suit (forcing, natural) if available,
    otherwise bid 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.gf_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 360

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=13)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        exclude = {opening_suit(ctx), my_response_suit(ctx)}
        rebid = partner_rebid(ctx)
        if not rebid.is_notrump:
            exclude.add(rebid.suit)
        bids: list[SuitBid] = [SuitBid(3, Suit.NOTRUMP)]
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES):
            if suit in exclude:
                continue
            bid = cheapest_bid_in_suit(suit, rebid)
            if bid is not None:
                bids.append(bid)
        return frozenset(bids)

    def select(self, ctx: BiddingContext) -> RuleResult:
        new_suit = find_new_suit_forcing(ctx)
        if new_suit is not None:
            rebid = partner_rebid(ctx)
            bid = cheapest_bid_in_suit(new_suit, rebid)
            assert bid is not None
            return RuleResult(
                bid=bid,
                rule_name=self.name,
                explanation=f"13+ HCP after reverse -- {bid} forcing",
                forcing=True,
            )
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="13+ HCP after reverse -- 3NT",
        )


class JumpInOwnSuitAfterReverse(Rule):
    """Jump in own suit after reverse -- invitational.

    1x->1y->2z(rev)->3y. 10-12 HCP, 6+ cards.
    """

    @property
    def name(self) -> str:
        return "reresponse.jump_own_suit_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 295

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=12), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"10-12 HCP, 6+ after reverse -- invite 3{suit.letter}",
        )


class TwoNTAfterReverse(Rule):
    """Bid 2NT after reverse -- natural, invitational.

    1x->1y->2z(rev)->2NT. 10-12 HCP, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 290

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=10, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-12 HCP after reverse -- invitational 2NT",
        )


class RebidOwnSuitAfterReverse(Rule):
    """Rebid own suit after reverse -- minimum catch-all.

    1x->1y->2z(rev)->2y. 6-9 HCP. Cheapest in own suit = minimum.
    Forced to bid (reverse is forcing one round). No suit-length
    requirement -- this is the catch-all for hands that cannot give
    preference to opener's first suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 198

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=9)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(my_response_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-9 HCP, minimum after reverse -- {bid}",
        )


class PreferenceAfterReverse(Rule):
    """Preference to opener's first suit after reverse -- minimum.

    1x->1y->2z(rev)->3x. 6-9 HCP, 3+ in opener's first suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_reverse"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 199

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, _partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(max_hcp=9), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(opening_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-9 HCP, preference to first suit after reverse -- {bid}",
        )


# ── F9: After Opener Jump Shifted (1x->1y->3z->?) ───────────────


class RaiseJumpShiftSuit(Rule):
    """Raise opener's jump shift suit.

    1x->1y->3z->4z or raise. GF, 4+ support for z.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_jump_shift_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 444

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return HasSuitFit(partner_rebid_suit, min_len=4)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(partner_rebid_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"4+ {suit.letter}, support opener's jump shift -- {bid}",
            forcing=True,
        )


class SupportOpenerFirstAfterJS(Rule):
    """Show support for opener's first suit after jump shift.

    1x->1y->3z->3x/4x. GF, 3+ in opening suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.support_opener_first_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 379

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return HasSuitFit(opening_suit, min_len=3)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(opening_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"3+ {suit.letter}, support opener's first suit -- {bid}",
            forcing=True,
        )


class RebidOwnSuitAfterJS(Rule):
    """Rebid own suit after jump shift.

    1x->1y->3z->3y/4y. GF, 6+ cards.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_js"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 378

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return my_response_suit_6plus

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        bid = cheapest_bid_in_suit(my_response_suit(ctx), partner_rebid(ctx))
        if bid is None:
            return frozenset()
        return frozenset({bid})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        assert bid is not None
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6+ {suit.letter}, rebid own suit after jump shift -- {bid}",
            forcing=True,
        )


class ThreeNTAfterJumpShift(Rule):
    """Bid 3NT after jump shift -- no clear fit.

    1x->1y->3z->3NT. Balanced, no fit.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_jump_shift"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 375

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_jump_shifted)

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No clear fit after jump shift -- 3NT",
        )


# ── F10: After Opener Bid 2NT (1x->1y->2NT->?) ─────────────────


class FourMAfter2NTRebid(Rule):
    """Bid game in own major after 2NT rebid.

    1x->1y->2NT->4M. 8+ HCP, 6+ card major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_2nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 343

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_rebid_2nt,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8), my_response_suit_6plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"8+ HCP, 6+ card major after 2NT -- 4{suit.letter}",
        )


class ThreeNTAfter2NTRebid(Rule):
    """Bid 3NT after opener's 2NT rebid.

    1x->1y->2NT->3NT. 8+ HCP (combined 26+).
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 339

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_2nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=8)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8+ HCP after 2NT rebid (combined 26+) -- 3NT",
        )


class ThreeSuitAfter2NTRebid(Rule):
    """Bid 3M after 2NT rebid -- forcing, lets opener choose 3NT or 4M.

    1x->1y->2NT->3y. 8+ HCP, 5+ card major.
    """

    @property
    def name(self) -> str:
        return "reresponse.3_suit_after_2nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 341

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            partner_rebid_2nt,
            i_responded_in_a_major,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8), my_response_suit_5plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"8+ HCP, 5+ {suit.letter} after 2NT --"
                f" 3{suit.letter} lets opener choose"
                f" 3NT or 4{suit.letter}"
            ),
            forcing=True,
        )


class PassAfter2NTRebid(Rule):
    """Pass after opener's 2NT rebid.

    1x->1y->2NT->Pass. 6-7 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_2nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 185

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_2nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=7)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-7 HCP after 2NT rebid -- pass",
        )


# ── F11: After Opener Bid 3NT (1x->1y->3NT->?) ─────────────────


class PassAfter3NTRebid(Rule):
    """Pass after opener's 3NT rebid -- game reached.

    1x->1y->3NT->Pass.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_3nt_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 90

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_new_suit_1level, partner_rebid_3nt)

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after 3NT rebid -- pass",
        )


# ── F12: After Opener Double-Jump Rebid Own Suit (1x->1y->4x->?) ──


class PassAfterDoubleJumpRebid(Rule):
    """Pass after opener's double-jump rebid of own suit.

    1x->1y->4x->Pass. Opener shows 19-21 with self-supporting 6+ suit.
    For majors (4H/4S), game is reached. For minors (4C/4D), pass is
    pragmatic -- opener bid aggressively and 5m is rarely right.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_double_jump_rebid"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 88

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_new_suit_1level,
            _partner_double_jump_rebid_own_suit,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Opener double-jump-rebid own suit -- pass",
        )
