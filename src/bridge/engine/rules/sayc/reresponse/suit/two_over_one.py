"""After 2-Over-1 Response (1x->2y->rebid->?)."""

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
    my_response_suit_5plus,
    my_response_suit_6plus,
    opening_bid,
    opening_is_major,
    opening_suit,
    partner_opened_1_suit,
    partner_raised_my_suit,
    partner_rebid,
    partner_rebid_2nt,
    partner_rebid_3nt,
    partner_rebid_new_suit,
    partner_rebid_own_suit,
    partner_rebid_suit,
    partner_reversed,
    stoppers_in_unbid,
)

__all__ = [
    # H1: After raise
    "ThreeNTAfterRaise2Over1",
    "FourMAfterRaise2Over1",
    "SlamTryMinorAfterRaise",
    "GameInMinorAfterRaise",
    "PassAfterMinorRaise2Over1",
    # H2: After rebid own suit
    "FourMAfter2Over1OwnSuit",
    "ThreeNTAfter2Over1OwnSuit",
    "NewSuitAfter2Over1OwnSuit",
    "RaiseOpenerAfter2Over1",
    "RebidOwnSuitAfter2Over1",
    "TwoNTAfter2Over1",
    # H3: After new suit non-reverse
    "FourMAfter2Over1NewSuit",
    "ThreeNTAfter2Over1NewSuit",
    "FourthSuitAfter2Over1NS",
    "RaiseOpenerNewSuit2Over1",
    "PreferenceAfter2Over1NS",
    "RebidOwnAfter2Over1NS",
    "TwoNTAfter2Over1NS",
    # H4: After 2NT
    "ThreeNTAfter2Over1_2NT",
    "ThreeSuitAfter2Over1_2NT",
    "PassAfter2Over1_2NT",
    # H5: After reverse
    "ThreeNTAfterReverse2Over1",
    "RaiseReverseSuit2Over1",
    "RebidOwnAfterReverse2Over1",
    "PreferenceAfterReverse2Over1",
    "TwoNTAfterReverse2Over1",
    # H6: After 3NT
    "PassAfter3NT2Over1",
]


# -- helpers --------------------------------------------


@condition("partner's new suit at 2-level")
def _partner_new_suit_at_2_level(ctx: BiddingContext) -> bool:
    """Partner's non-reverse new suit rebid is at the 2-level (not 3)."""
    return partner_rebid(ctx).level == 2


@condition("I bid 2-over-1")
def _i_bid_2_over_1(ctx: BiddingContext) -> bool:
    """I bid a new suit at the 2-level (not a jump shift)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    if resp.level != 2 or resp.is_notrump or resp.suit == opening.suit:
        return False
    # Not a jump shift: check if this was the cheapest level for this suit
    cheapest = cheapest_bid_in_suit(resp.suit, opening)
    return cheapest is not None and resp.level == cheapest.level


# -- H1: After Opener Raised My Suit (1x->2y->3y->?) --------------


class ThreeNTAfterRaise2Over1(Rule):
    """Bid 3NT after raise of 2-over-1 -- minor suit.

    1x->2y->3y->3NT. 10-14 HCP, balanced, minor, stoppers.
    3NT (9 tricks) is far easier than 5m (11 tricks) when balanced.
    Priority above GameInMinorAfterRaise so 13-14 balanced prefers 3NT.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_raise_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 385

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            i_responded_in_a_minor,
            partner_raised_my_suit,
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=10, max_hcp=14), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-14 HCP, balanced, minor raised -- 3NT",
        )


class FourMAfterRaise2Over1(Rule):
    """Bid game in major after raise of 2-over-1.

    1S->2H->3H->4H. 10+ HCP, major raised.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_raise_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 365

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            i_responded_in_a_major,
            partner_raised_my_suit,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=10)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"10+ HCP, major raised -- game in 4{suit.letter}",
        )


class SlamTryMinorAfterRaise(Rule):
    """Slam try after minor raise.

    1x->2y->3y->4y. 15+ HCP, minor, slam interest.
    Below game -- forcing, invites cue-bidding.
    """

    @property
    def name(self) -> str:
        return "reresponse.slam_try_minor_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 445

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            i_responded_in_a_minor,
            partner_raised_my_suit,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=15)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"15+ HCP, minor raised -- slam try 4{suit.letter}",
            forcing=True,
        )


class GameInMinorAfterRaise(Rule):
    """Bid game in minor after raise.

    1x->2y->3y->5y. 13-14 HCP, minor, no slam interest.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_in_minor_after_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 380

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            i_responded_in_a_minor,
            partner_raised_my_suit,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=13, max_hcp=14)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(5, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"13-14 HCP, minor raised -- game 5{suit.letter}",
        )


class PassAfterMinorRaise2Over1(Rule):
    """Pass after minor raise -- no game prospects.

    1x->2y->3y->Pass. 10-12 HCP, minor.
    Not balanced or no stoppers, so 3NT is not viable.
    Combined 22-24 HCP is not enough for 5m.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_minor_raise_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 186

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            i_responded_in_a_minor,
            partner_raised_my_suit,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=10, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="10-12 HCP, minor raised, no game -- pass",
        )


# -- H2: After Opener Rebid Own Suit (1x->2y->2x->?) -------------


class FourMAfter2Over1OwnSuit(Rule):
    """Bid game in major after opener rebid own suit.

    1x->2y->2x->4M. 12+ HCP, 3+ support, major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_2over1_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 373

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            opening_is_major,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"12+ HCP, 3+ support -- game in 4{suit.letter}",
        )


class ThreeNTAfter2Over1OwnSuit(Rule):
    """Bid 3NT after opener rebid own suit.

    1x->2y->2x->3NT. 12+ HCP, balanced, stoppers.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2over1_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 363

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_own_suit)

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=12), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12+ HCP, balanced -- 3NT",
        )


class NewSuitAfter2Over1OwnSuit(Rule):
    """Bid a new suit forcing after opener rebid own suit.

    1x->2y->2x->new suit. 12+ HCP, 4+ cards in new suit.
    Only 2 suits bid so far -- this introduces a third suit to explore.
    """

    def __init__(self) -> None:
        self._new_suit = SuitFinderComputed(
            find_new_suit_forcing,
            "4+ card new suit",
            min_len=4,
        )

    @property
    def name(self) -> str:
        return "reresponse.new_suit_after_2over1_own_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 359

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_own_suit)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12), self._new_suit)

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
            explanation=f"12+ HCP, new suit forcing -- {bid}",
            forcing=True,
        )


class RaiseOpenerAfter2Over1(Rule):
    """Raise opener's suit after 2-over-1 -- invitational.

    1x->2y->2x->3x. 10-12 HCP, 3+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_opener_after_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 291

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_own_suit)

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=10, max_hcp=12), HasSuitFit(opening_suit, min_len=3)
        )

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
            explanation=f"10-12 HCP, 3+ {suit.letter} -- invitational raise {bid}",
        )


class RebidOwnSuitAfter2Over1(Rule):
    """Rebid own suit after 2-over-1 -- invitational.

    1x->2y->2x->3y. 10-12 HCP, 6+ cards.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_suit_after_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 288

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_own_suit)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=12), my_response_suit_6plus)

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
            explanation=f"10-12 HCP, 6+ cards -- invitational {bid}",
        )


class TwoNTAfter2Over1(Rule):
    """Bid 2NT after opener rebid own suit -- invitational.

    1x->2y->2x->2NT. 10-12 HCP, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 285

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_own_suit)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=10, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-12 HCP after 2-over-1 -- invitational 2NT",
        )


# -- H3: After Opener Bid New Suit (1x->2y->2z->?) ---------------


class ThreeNTAfter2Over1NewSuit(Rule):
    """Bid 3NT after opener's new suit in 2-over-1.

    1x->2y->2z->3NT. 12+ HCP, balanced, fourth suit stopped.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2over1_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 364

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_new_suit)

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=12), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12+ HCP, balanced -- 3NT",
        )


class FourthSuitAfter2Over1NS(Rule):
    """Fourth suit forcing after opener's new suit in 2-over-1.

    1x->2y->2z->fourth suit. 12+ HCP.
    """

    def __init__(self) -> None:
        self._fsf = Computed(find_fourth_suit_bid, "fourth suit available")

    @property
    def name(self) -> str:
        return "reresponse.fourth_suit_after_2over1_ns"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 358

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_new_suit)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12), self._fsf)

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
            explanation=f"12+ HCP, fourth suit forcing -- {bid}",
            forcing=True,
        )


class RaiseOpenerNewSuit2Over1(Rule):
    """Raise opener's new suit in 2-over-1.

    1x->2y->2z->3z. 10+ HCP, 4+ in z.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_opener_new_suit_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 296

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_new_suit)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10), HasSuitFit(partner_rebid_suit, min_len=4))

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
            explanation=f"10+ HCP, 4+ {suit.letter} -- raise {bid}",
        )


class FourMAfter2Over1NewSuit(Rule):
    """Bid game in opener's major after new suit in 2-over-1.

    1x->2y->2z->4M. 12+ HCP, 3+ support for opener's major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_2over1_new_suit"

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
            opening_is_major,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
        )

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=12), HasSuitFit(opening_suit, min_len=3))

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"12+ HCP, 3+ support -- game in 4{suit.letter}",
        )


class PreferenceAfter2Over1NS(Rule):
    """Preference to opener's first suit after new suit in 2-over-1.

    1x->2y->2z->cheapest x. 10-12 HCP, 3+ in opener's first suit.
    Shows bottom of 2-over-1 range with preference.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_2over1_ns"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 287

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_new_suit)

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=10, max_hcp=12), HasSuitFit(opening_suit, min_len=3)
        )

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
            explanation=f"10-12 HCP, preference to opener's first suit -- {bid}",
        )


class RebidOwnAfter2Over1NS(Rule):
    """Rebid own suit after opener's new suit in 2-over-1.

    1x->2y->2z->3y. 10-12 HCP, 6+ cards.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_after_2over1_ns"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 289

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_new_suit)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=12), my_response_suit_6plus)

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
            explanation=f"10-12 HCP, 6+ cards -- rebid {bid}",
        )


class TwoNTAfter2Over1NS(Rule):
    """Bid 2NT after opener's new suit in 2-over-1.

    1x->2y->2z->2NT. 10-12 HCP. Only when opener's new suit is
    at the 2-level (so 2NT is a legal bid above it).
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_2over1_ns"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 284

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            _partner_new_suit_at_2_level,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=10, max_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-12 HCP after new suit 2-over-1 -- invitational 2NT",
        )


# -- H4: After Opener Bid 2NT (1x->2y->2NT->?) -------------------


class ThreeNTAfter2Over1_2NT(Rule):
    """Bid 3NT after opener's 2NT in 2-over-1.

    1x->2y->2NT->3NT. 12+ HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2over1_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 353

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_2nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=12)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12+ HCP after 2NT -- 3NT (combined 24+)",
        )


class ThreeSuitAfter2Over1_2NT(Rule):
    """Bid a suit at 3-level after opener's 2NT in 2-over-1.

    1x->2y->2NT->3-suit. 10-12 HCP, 5+ in a suit, exploring.
    """

    @property
    def name(self) -> str:
        return "reresponse.3_suit_after_2over1_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 294

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_2nt)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=12), my_response_suit_5plus)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, my_response_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"10-12 HCP, 5+ cards -- exploring 3{suit.letter}",
            forcing=True,
        )


class PassAfter2Over1_2NT(Rule):
    """Pass after opener's 2NT in 2-over-1.

    1x->2y->2NT->Pass. 10-11 HCP, balanced.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_2over1_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 189

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_2nt)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=11)

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="10-11 HCP, content with 2NT -- pass",
        )


# -- H5: After Opener Reversed (1x->2y->reverse->?) ---------------
# Reverse shows 17+ HCP and is forcing one round. Combined 27+ HCP.
# Possible auctions: 1D->2C->2H, 1D->2C->2S, 1H->2C->2S, 1H->2D->2S


class ThreeNTAfterReverse2Over1(Rule):
    """Bid 3NT after opener reversed in 2-over-1.

    1x->2y->reverse->3NT. 12+ HCP, balanced, stoppers.
    Combined 29+ HCP, game is clear.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_reverse_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 366

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=12), Balanced())

    def possible_bids(self, ctx: BiddingContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12+ HCP, balanced after reverse -- 3NT",
        )


class RaiseReverseSuit2Over1(Rule):
    """Raise the reverse suit in 2-over-1.

    1x->2y->2z(rev)->3z. 10+ HCP, 4+ in reverse suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_reverse_suit_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 297

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10), HasSuitFit(partner_rebid_suit, min_len=4))

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
            explanation=f"10+ HCP, 4+ {suit.letter} -- raise reverse suit {bid}",
        )


class RebidOwnAfterReverse2Over1(Rule):
    """Rebid own suit after reverse in 2-over-1.

    1x->2y->2z(rev)->3y. 10-12 HCP, 6+ cards.
    Invitational -- shows a good suit and minimum of 2-over-1 range.
    """

    @property
    def name(self) -> str:
        return "reresponse.rebid_own_after_reverse_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 293

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=12), my_response_suit_6plus)

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
            explanation=f"10-12 HCP, 6+ cards after reverse -- invite {bid}",
        )


class PreferenceAfterReverse2Over1(Rule):
    """Preference to opener's first suit after reverse in 2-over-1.

    1x->2y->2z(rev)->cheapest x. 10-12 HCP, 3+ in opener's first suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_reverse_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 288

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_reversed)

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=10, max_hcp=12), HasSuitFit(opening_suit, min_len=3)
        )

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
            explanation=f"10-12 HCP, preference to first suit after reverse -- {bid}",
        )


class TwoNTAfterReverse2Over1(Rule):
    """Bid 2NT after reverse in 2-over-1 -- invitational catch-all.

    1x->2y->2z(rev)->2NT. 10-12 HCP.
    Catch-all when no suit fit or long suit to rebid.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_reverse_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 286

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_reversed)

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


# -- H6: After Opener Bid 3NT (1x->2y->3NT->?) --------------------
# Opener shows 18-19 HCP balanced. Game is reached. Combined 28-31+ HCP.


class PassAfter3NT2Over1(Rule):
    """Pass after opener's 3NT in 2-over-1.

    1x->2y->3NT->Pass. Game reached, no slam interest.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_3nt_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 91

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1_suit, _i_bid_2_over_1, partner_rebid_3nt)

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: BiddingContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after 3NT -- pass",
        )
