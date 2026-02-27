"""Section G: After I Responded 1NT (1x->1NT->rebid->?)."""

from __future__ import annotations

from bridge.engine.bidutil import cheapest_bid_in_suit
from bridge.engine.condition import All, HasSuitFit, HcpRange, condition
from bridge.engine.context import BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, SuitBid
from bridge.model.card import Suit

from .helpers import (
    my_response,
    opening_is_major,
    opening_suit,
    partner_game_in_own_suit,
    partner_jump_rebid_own_suit,
    partner_jump_shifted,
    partner_opened_1_suit,
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
    "FourMAfterJumpRebidOver1NT",
    "PassAfter2NTOver1NT",
    "PassAfter3NTOver1NT",
    "PassAfterGameJumpOver1NT",
    "PassAfterJumpRebidOver1NT",
    "PassAfterNewSuit1NT",
    "PassAfterSuitRebid1NT",
    "PreferenceAfterReverseOver1NT",
    "PreferenceTo1stSuit1NT",
    "RaiseNewSuit1NTResponse",
    "RaiseReverseSuitOver1NT",
    "ReturnToOpenerSuitAfterJS1NT",
    "SupportJumpShiftOver1NT",
    "ThreeNTAfter2NTOver1NT",
    "ThreeNTAfterJSOver1NT",
    "ThreeNTAfterJumpRebidOver1NT",
    "ThreeNTAfterReverseOver1NT",
    "TwoNTAfterReverseOver1NT",
]


# ── Section G helpers ─────────────────────────────────


@condition("I responded 1NT")
def _i_bid_1nt(ctx: BiddingContext) -> bool:
    resp = my_response(ctx)
    return resp.is_notrump and resp.level == 1


class PassAfterSuitRebid1NT(Rule):
    """Pass after opener rebid own suit over 1NT.

    1x->1NT->2x->Pass. Content with partscore.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_suit_rebid_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 94

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_own_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="After 1NT response, opener rebid own suit -- pass",
        )


class RaiseNewSuit1NTResponse(Rule):
    """Raise opener's new suit after 1NT response -- invitational.

    1x->1NT->2z->3z. 8-10 HCP, 4+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_new_suit_1nt_response"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 279

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_new_suit,
            HcpRange(min_hcp=8, max_hcp=10),
            HasSuitFit(partner_rebid_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"8-10 HCP, 4+ {suit.letter} -- invitational raise {bid}",
        )


class PreferenceTo1stSuit1NT(Rule):
    """Preference to opener's first suit after 1NT.

    1x->1NT->2z->2x. 6-10 HCP, 3+ in opener's first suit.
    Only when first suit ranks higher than second suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_to_1st_suit_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 197

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_new_suit,
            HasSuitFit(opening_suit, min_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"6-10 HCP, 3+ {suit.letter} -- preference to first suit {bid}",
        )


class PassAfterNewSuit1NT(Rule):
    """Pass with tolerance for opener's new suit after 1NT.

    1x->1NT->2z->Pass. 6-10 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_new_suit_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 95

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_new_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-10 HCP, tolerance for new suit -- pass",
        )


class ThreeNTAfter2NTOver1NT(Rule):
    """Accept 2NT invitation after 1NT response.

    1x->1NT->2NT->3NT. 8-10 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 331

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_2nt,
            HcpRange(min_hcp=8, max_hcp=10),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8-10 HCP, accept 2NT invitation -- 3NT",
        )


class PassAfter2NTOver1NT(Rule):
    """Decline 2NT invitation after 1NT response.

    1x->1NT->2NT->Pass. 6-7 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_2nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 186

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_2nt,
            HcpRange(max_hcp=7),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-7 HCP, decline 2NT invitation -- pass",
        )


class FourMAfterJumpRebidOver1NT(Rule):
    """Accept jump rebid invitation in major.

    1x->1NT->3x->4M. 8-10 HCP, 2+ support, major.
    """

    @property
    def name(self) -> str:
        return "reresponse.4m_after_jump_rebid_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 335

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            opening_is_major,
            _i_bid_1nt,
            partner_jump_rebid_own_suit,
            HcpRange(min_hcp=8, max_hcp=10),
            HasSuitFit(opening_suit, min_len=2),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=f"8-10 HCP, 2+ support -- accept, 4{suit.letter}",
        )


class ThreeNTAfterJumpRebidOver1NT(Rule):
    """Accept jump rebid invitation in NT.

    1x->1NT->3x->3NT. 8-10 HCP, no major support.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_jump_rebid_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 333

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_jump_rebid_own_suit,
            HcpRange(min_hcp=8, max_hcp=10),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8-10 HCP, accept jump rebid -- 3NT",
        )


class PassAfterJumpRebidOver1NT(Rule):
    """Decline jump rebid invitation after 1NT response.

    1x->1NT->3x->Pass. 6-7 HCP.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_jump_rebid_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 183

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_jump_rebid_own_suit,
            HcpRange(max_hcp=7),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="6-7 HCP, decline jump rebid -- pass",
        )


class PassAfter3NTOver1NT(Rule):
    """Pass after opener bid 3NT over 1NT response.

    1x->1NT->3NT->Pass. Game reached.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_3nt_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 91

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_rebid_3nt,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after 3NT -- pass",
        )


class SupportJumpShiftOver1NT(Rule):
    """Support opener's jump shift suit after 1NT.

    1x->1NT->3z->raise. GF, 4+ in z.
    """

    @property
    def name(self) -> str:
        return "reresponse.support_jump_shift_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 377

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_jump_shifted,
            HasSuitFit(partner_rebid_suit, min_len=4),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"4+ {suit.letter}, support jump shift -- {bid}",
            forcing=True,
        )


class ThreeNTAfterJSOver1NT(Rule):
    """Bid 3NT after jump shift over 1NT -- no fit.

    1x->1NT->3z->3NT. Fallback when no suit fit exists.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_js_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 374

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_jump_shifted,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="No fit after jump shift over 1NT -- 3NT",
        )


class ReturnToOpenerSuitAfterJS1NT(Rule):
    """Return to opener's first suit after jump shift over 1NT.

    1x->1NT->3z->3x/4x. 3+ in opening suit.
    """

    @property
    def name(self) -> str:
        return "reresponse.return_to_opener_suit_after_js_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 376

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_jump_shifted,
            HasSuitFit(opening_suit, min_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"3+ {suit.letter}, belated support after JS -- {bid}",
            forcing=True,
        )


# ── After reverse (1x->1NT->2z where z>x, 17+, forcing) ────────


class ThreeNTAfterReverseOver1NT(Rule):
    """Bid 3NT after opener reversed over 1NT.

    1x->1NT->2z(rev)->3NT. 8-10 HCP, stoppers in unbid suits.
    """

    @property
    def name(self) -> str:
        return "reresponse.3nt_after_reverse_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 336

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_reversed,
            HcpRange(min_hcp=8, max_hcp=10),
            stoppers_in_unbid,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="8-10 HCP, stoppers after reverse -- 3NT",
        )


class RaiseReverseSuitOver1NT(Rule):
    """Raise opener's reverse suit after 1NT response.

    1x->1NT->2z(rev)->3z. 8-10 HCP, 3+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.raise_reverse_suit_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 277

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_reversed,
            HcpRange(min_hcp=8, max_hcp=10),
            HasSuitFit(partner_rebid_suit, min_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = partner_rebid_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"8-10 HCP, 3+ {suit.letter} -- raise reverse suit {bid}",
        )


class PreferenceAfterReverseOver1NT(Rule):
    """Preference to opener's first suit after reverse over 1NT.

    1x->1NT->2z(rev)->3x. 3+ in opener's first suit.
    Opener's first suit is longer (reverse guarantees this).
    """

    @property
    def name(self) -> str:
        return "reresponse.preference_after_reverse_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 100

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_reversed,
            HasSuitFit(opening_suit, min_len=3),
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = opening_suit(ctx)
        rebid = partner_rebid(ctx)
        bid = cheapest_bid_in_suit(suit, rebid)
        return RuleResult(
            bid=bid,
            rule_name=self.name,
            explanation=f"3+ {suit.letter}, preference after reverse -- {bid}",
        )


class TwoNTAfterReverseOver1NT(Rule):
    """Bid 2NT after reverse over 1NT -- minimum, forced.

    1x->1NT->2z(rev)->2NT. Catch-all minimum response.
    Reverse is forcing one round; 2NT shows no direction.
    """

    @property
    def name(self) -> str:
        return "reresponse.2nt_after_reverse_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 83

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_reversed,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="Minimum after reverse, forced -- 2NT",
        )


# ── After game jump (1x->1NT->4x) ───────────────────────────────


class PassAfterGameJumpOver1NT(Rule):
    """Pass after opener jumped to game in own suit over 1NT.

    1x->1NT->4x->Pass. Game reached.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_after_game_jump_over_1nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 82

    @property
    def conditions(self) -> All:
        return All(
            partner_opened_1_suit,
            _i_bid_1nt,
            partner_game_in_own_suit,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation="Game reached after jump to game -- pass",
        )
