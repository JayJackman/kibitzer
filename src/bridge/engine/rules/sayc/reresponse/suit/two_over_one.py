"""Section H: After 2-Over-1 Response (1x->2y->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import (
    All,
    Balanced,
    Computed,
    HasSuitFit,
    HcpRange,
    condition,
)
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

from .helpers import (
    find_fourth_suit_bid,
    find_new_suit_forcing,
    my_response,
    my_response_suit,
    my_response_suit_5plus,
    my_response_suit_6plus,
    my_response_suit_is_major,
    my_response_suit_is_minor,
    opening_bid,
    opening_is_major,
    opening_suit,
    partner_opened_1_suit,
    partner_raised_my_suit,
    partner_rebid,
    partner_rebid_2nt,
    partner_rebid_new_suit,
    partner_rebid_own_suit,
    partner_rebid_suit,
    stoppers_in_unbid,
)

__all__ = [
    "FourMAfter2Over1OwnSuit",
    "FourMAfterRaise2Over1",
    "FourthSuitAfter2Over1NS",
    "GameInMinorAfterRaise",
    "NewSuitAfter2Over1OwnSuit",
    "PassAfter2Over1_2NT",
    "RaiseOpenerAfter2Over1",
    "RaiseOpenerNewSuit2Over1",
    "RebidOwnAfter2Over1NS",
    "RebidOwnSuitAfter2Over1",
    "SlamTryMinorAfterRaise",
    "ThreeNTAfter2Over1NewSuit",
    "ThreeNTAfter2Over1OwnSuit",
    "ThreeNTAfter2Over1_2NT",
    "ThreeNTAfterRaise2Over1",
    "ThreeSuitAfter2Over1_2NT",
    "TwoNTAfter2Over1",
    "TwoNTAfter2Over1NS",
]


# -- Section H helpers --------------------------------------------


@condition("I bid 2-over-1")
def _i_bid_2_over_1(ctx: BiddingContext) -> bool:
    """I bid a new suit at the 2-level (not a jump shift)."""
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    if resp.level != 2 or resp.is_notrump or resp.suit == opening.suit:
        return False
    # Not a jump shift: check if this was the cheapest level for this suit
    cheapest = cheapest_bid_in_suit(resp.suit, opening)
    return resp.level == cheapest.level


# -- H1: After Opener Raised My Suit (1x->2y->3y->?) --------------


class ThreeNTAfterRaise2Over1(Rule):
    """Bid 3NT after raise of 2-over-1 -- minor suit.

    1x->2y->3y->3NT. 10-12 HCP, balanced, minor.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_raise_2over1"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 351

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            my_response_suit_is_minor,
            partner_raised_my_suit,
            stoppers_in_unbid,
            HcpRange(min_hcp=10, max_hcp=12),
            Balanced(),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="10-12 HCP, balanced, minor raised -- 3NT",
        )


class FourMAfterRaise2Over1(Rule):
    """Bid game in major after raise of 2-over-1.

    1x->2y->3y->4M. 10+ HCP, major or major fit.
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            my_response_suit_is_major,
            partner_raised_my_suit,
            HcpRange(min_hcp=10),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            my_response_suit_is_minor,
            partner_raised_my_suit,
            HcpRange(min_hcp=15),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            my_response_suit_is_minor,
            partner_raised_my_suit,
            HcpRange(min_hcp=13, max_hcp=14),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"13-14 HCP, minor raised -- game 5{suit.letter}",
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            opening_is_major,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            HcpRange(min_hcp=12),
            HasSuitFit(opening_suit, min_len=3),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            stoppers_in_unbid,
            HcpRange(min_hcp=12),
            Balanced(),
        )

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
        self._new_suit = Computed(find_new_suit_forcing, "4+ card new suit")

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            HcpRange(min_hcp=12),
            self._new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._new_suit.value
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            HcpRange(min_hcp=10, max_hcp=12),
            HasSuitFit(opening_suit, min_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            HcpRange(min_hcp=10, max_hcp=12),
            my_response_suit_6plus,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_own_suit,
            HcpRange(min_hcp=10, max_hcp=12),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            stoppers_in_unbid,
            HcpRange(min_hcp=12),
            Balanced(),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            HcpRange(min_hcp=12),
            self._fsf,
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            HcpRange(min_hcp=10),
            HasSuitFit(partner_rebid_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"10+ HCP, 4+ {suit.letter} -- raise {bid}",
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            HcpRange(min_hcp=10, max_hcp=12),
            my_response_suit_6plus,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = my_response_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"10-12 HCP, 6+ cards -- rebid {bid}",
        )


class TwoNTAfter2Over1NS(Rule):
    """Bid 2NT after opener's new suit in 2-over-1.

    1x->2y->2z->2NT. 10-12 HCP, balanced.
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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_new_suit,
            HcpRange(min_hcp=10, max_hcp=12),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_2nt,
            HcpRange(min_hcp=12),
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_2nt,
            HcpRange(min_hcp=10, max_hcp=12),
            my_response_suit_5plus,
        )

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
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_2_over_1,
            partner_rebid_2nt,
            HcpRange(max_hcp=11),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="10-11 HCP, content with 2NT -- pass",
        )
