"""Section B: After I Raised Opener's Minor (1m->2m->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import All, Condition, HasSuitFit, HcpRange, condition
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    i_raised,
    my_response,
    opening_bid,
    opening_suit,
    partner_opened_1_suit,
    partner_rebid,
    partner_rebid_2nt,
    partner_rebid_3nt,
    partner_rebid_suit,
    stoppers_in_unbid,
)

__all__ = [
    "Accept2NTAfterMinorRaise",
    "AcceptMinorInvite",
    "Decline2NTAfterMinorRaise",
    "DeclineMinorInvite",
    "PassAfterMinor3NT",
    "PassAfterMinorGame",
    "Raise2ndSuitAfterMinorRaise",
    "ReturnToMinor",
    "ThreeNTAfterMinorNewSuit",
]


# ── Section B helpers ─────────────────────────────────


@condition("opening suit is minor")
def _opening_is_minor(ctx: BiddingContext) -> bool:
    return opening_suit(ctx).is_minor


@condition("partner bid new suit after my minor raise")
def _partner_bid_new_suit_over_raise(ctx: BiddingContext) -> bool:
    """Partner bid a new suit after I single-raised a minor.

    After a raise the reverse/non-reverse distinction does not apply --
    any new suit (not the opening suit, not NT) counts.
    e.g. 1D->2D->2H, 1C->2C->2D, 1D->2D->3C.
    """
    if not i_raised(ctx):
        return False
    opening = opening_bid(ctx)
    resp = my_response(ctx)
    rebid = partner_rebid(ctx)
    return (
        opening.suit.is_minor
        and not rebid.is_notrump
        and rebid.suit != opening.suit
        and rebid.suit != resp.suit
    )


@condition("partner invited in our minor")
def _partner_invited_minor(ctx: BiddingContext) -> bool:
    """Partner re-raised our minor to the 3-level (1m->2m->3m)."""
    if not i_raised(ctx):
        return False
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return opening.suit.is_minor and rebid.suit == opening.suit and rebid.level == 3


@condition("partner bid game in our minor")
def _partner_bid_game_minor(ctx: BiddingContext) -> bool:
    """Partner jumped to 5m after my raise (1m->2m->5m)."""
    if not i_raised(ctx):
        return False
    opening = opening_bid(ctx)
    rebid = partner_rebid(ctx)
    return opening.suit.is_minor and rebid.suit == opening.suit and rebid.level == 5


# ── Rules ─────────────────────────────────────────────


class PassAfterMinor3NT(Rule):
    """Pass after opener bid 3NT over minor raise.

    1m->2m->3NT->Pass.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_minor_3nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 93

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            partner_rebid_3nt,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Opener placed 3NT after minor raise -- pass",
        )


class Accept2NTAfterMinorRaise(Rule):
    """Accept 2NT invitation after minor raise.

    1m->2m->2NT->3NT. 9-10 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_2nt_after_minor_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 299

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            partner_rebid_2nt,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=9, max_hcp=10)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="9-10 HCP, accept 2NT invitation -- 3NT",
        )


class Decline2NTAfterMinorRaise(Rule):
    """Decline 2NT invitation after minor raise.

    1m->2m->2NT->3m. 6-8 HCP, return to minor.
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_2nt_after_minor_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 190

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            partner_rebid_2nt,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=8)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=f"6-8 HCP, decline 2NT -- return to 3{suit.letter}",
        )


class ThreeNTAfterMinorNewSuit(Rule):
    """Bid 3NT after opener's new suit over minor raise.

    1m->2m->2x->3NT. 9-10 HCP with stoppers.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_minor_new_suit"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 298

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_bid_new_suit_over_raise,
        )

    @property
    def conditions(self) -> Condition:
        return All(stoppers_in_unbid, HcpRange(min_hcp=9, max_hcp=10))

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="9-10 HCP, stoppers after minor new suit -- 3NT",
        )


class Raise2ndSuitAfterMinorRaise(Rule):
    """Raise opener's second suit after minor raise.

    1m->2m->2x->3x. 8-10 HCP, 4+ support for new suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_2nd_suit_after_minor_raise"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 293

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_bid_new_suit_over_raise,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=8, max_hcp=10),
            HasSuitFit(partner_rebid_suit, min_len=4),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        suit = partner_rebid_suit(ctx)
        bid = cheapest_bid_in_suit(suit, partner_rebid(ctx))
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
            explanation=f"8-10 HCP, 4+ {suit.letter} -- raise opener's second suit",
        )


class ReturnToMinor(Rule):
    """Return to agreed minor after opener's new suit.

    1m->2m->2x->3m. 6-10 HCP, catch-all when no fit or stoppers.
    Higher-priority rules intercept hands with stoppers (3NT)
    or 4+ fit (raise new suit).
    """

    @property
    def name(self) -> str:
        return "reresponse.return_to_minor"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 182

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_bid_new_suit_over_raise,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=10)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
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
            explanation=f"Return to agreed minor -- {bid}",
        )


class AcceptMinorInvite(Rule):
    """Accept minor invite -- bid 3NT or 5m.

    1m->2m->3m->3NT/5m. 9-10 HCP.
    With stoppers in unbid suits, bid 3NT. Otherwise bid 5m.
    """

    @property
    def name(self) -> str:
        return "reresponse.accept_minor_invite"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 270

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_invited_minor,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=9, max_hcp=10)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP), SuitBid(5, opening_suit(ctx))})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        if stoppers_in_unbid(ctx):
            return RuleResult(
                bid=SuitBid(3, Suit.NOTRUMP),
                rule_name=self.name,
                explanation="9-10 HCP, stoppers -- accept minor invite with 3NT",
            )
        return RuleResult(
            bid=SuitBid(5, suit),
            rule_name=self.name,
            explanation=f"9-10 HCP, no stoppers -- accept invite 5{suit.letter}",
        )


class DeclineMinorInvite(Rule):
    """Decline minor invite -- pass.

    1m->2m->3m->Pass. 6-8 HCP, decline invitation.
    """

    @property
    def name(self) -> str:
        return "reresponse.decline_minor_invite"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 181

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_invited_minor,
        )

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=8)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-8 HCP, decline minor invite -- pass",
        )


class PassAfterMinorGame(Rule):
    """Pass after opener bid game in minor.

    1m->2m->5m->Pass. Game reached.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_minor_game"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 84

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1_suit,
            _opening_is_minor,
            i_raised,
            _partner_bid_game_minor,
        )

    @property
    def conditions(self) -> Condition:
        return All()

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached in minor -- pass",
        )
