"""Responder's rebid after Jacoby transfer over 1NT or 2NT -- SAYC.

Covers all reresponse decisions after responder used a Jacoby transfer
(2D/2H over 1NT, 3D/3H over 2NT) and opener completed or super-accepted.

Reference: research/05-conventions.md lines 68-114.
"""

from __future__ import annotations

from bridge.engine.condition import (
    All,
    Condition,
    HasSuitFit,
    HcpRange,
    SuitLength,
)
from bridge.engine.context import AuctionContext, BiddingContext
from bridge.engine.rule import Category, Rule, RuleResult
from bridge.model.bid import PASS, PassBid, SuitBid
from bridge.model.card import Suit

from .helpers import (
    i_bid_transfer_1nt,
    i_bid_transfer_2nt,
    partner_completed_transfer,
    partner_opened_1nt,
    partner_opened_2nt,
    partner_super_accepted,
    transfer_is_hearts,
    transfer_is_spades,
    transfer_suit,
)

__all__ = [
    # Section E: After normal transfer completion over 1NT
    "PassTransferSignoff",
    "Invite2NTAfterTransfer",
    "InviteRaiseTransfer",
    "InviteMajors55",
    "Game3NTAfterTransfer",
    "GameRaiseTransfer",
    "GFMajors55",
    # Section F: After super-accept over 1NT
    "PassSuperAccept",
    "Game3NTSuperAccept",
    "Game4MSuperAccept",
    "Quant4NTSuperAccept",
    # Section G: After transfer completion over 2NT
    "PassTransfer2NTSignoff",
    "Game3NTTransfer2NT",
    "Game4MTransfer2NT",
    "Quant4NTTransfer2NT",
]


# ── helpers ─────────────────────────────────────────────────────

_transfer_suit_5_exact = HasSuitFit(transfer_suit, min_len=5, max_len=5)
_transfer_suit_6_plus = HasSuitFit(transfer_suit, min_len=6)


# ── Section E: After normal transfer completion over 1NT ────────


class PassTransferSignoff(Rule):
    """Pass after transfer completion with a weak hand.

    1NT - 2D - 2H - Pass (or 1NT - 2H - 2S - Pass).
    0-7 HCP.  Sign-off in the major at the 2-level.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_transfer_signoff"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 50

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=7)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation=f"Weak hand -- sign-off in 2{suit.letter} after transfer",
        )


class Invite2NTAfterTransfer(Rule):
    """Invite with 2NT after transfer completion (5-card suit).

    1NT - 2D - 2H - 2NT (or 1NT - 2H - 2S - 2NT).
    8-9 HCP, exactly 5 cards in the transfer suit.
    Invitational -- opener passes, bids 3NT, or corrects to 3M.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_2nt_after_transfer"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 238

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), _transfer_suit_5_exact)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(2, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(f"8-9 HCP, 5-card {suit.name.lower()} -- invitational 2NT"),
        )


class InviteRaiseTransfer(Rule):
    """Invite by raising the transfer suit to the 3-level.

    1NT - 2D - 2H - 3H (or 1NT - 2H - 2S - 3S).
    8-9 HCP, 6+ cards in the transfer suit.
    Invitational -- opener passes or bids game.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_raise_transfer"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 242

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=9), _transfer_suit_6_plus)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        suit = transfer_suit(ctx)
        return frozenset({SuitBid(3, suit)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, suit),
            rule_name=self.name,
            explanation=(
                f"8-9 HCP, 6+ {suit.name.lower()} -- "
                f"invitational raise to 3{suit.letter}"
            ),
        )


class InviteMajors55(Rule):
    """Show 5-5 in the majors at invitational strength.

    1NT - 2D - 2H - 2S.  Transferred to hearts, then bid 2S to show
    5+ spades as well.  8-9 HCP.  Opener chooses the better major fit.
    SAYC convention: transfer to hearts first, then bid 2S = invitational 5-5.
    """

    @property
    def name(self) -> str:
        return "reresponse.invite_majors_55"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 244

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1nt,
            i_bid_transfer_1nt,
            partner_completed_transfer,
            transfer_is_hearts,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=8, max_hcp=9),
            SuitLength(Suit.HEARTS, min_len=5),
            SuitLength(Suit.SPADES, min_len=5),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(2, Suit.SPADES)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(2, Suit.SPADES),
            rule_name=self.name,
            explanation="8-9 HCP, 5-5 in majors -- invitational, showing both",
        )


class Game3NTAfterTransfer(Rule):
    """Bid 3NT with game values and a 5-card transfer suit.

    1NT - 2D - 2H - 3NT (or 1NT - 2H - 2S - 3NT).
    10-15 HCP, exactly 5 cards in the transfer suit.
    Opener may pass 3NT or correct to 4M with 3+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_after_transfer"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 338

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), _transfer_suit_5_exact)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                f"10-15 HCP, 5-card {suit.name.lower()} -- "
                f"3NT (opener may correct to 4{suit.letter})"
            ),
        )


class GameRaiseTransfer(Rule):
    """Raise the transfer suit to game.

    1NT - 2D - 2H - 4H (or 1NT - 2H - 2S - 4S).
    10-15 HCP, 6+ cards in the transfer suit.
    Game sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_raise_transfer"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 342

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=10, max_hcp=15), _transfer_suit_6_plus)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        suit = transfer_suit(ctx)
        return frozenset({SuitBid(4, suit)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"10-15 HCP, 6+ {suit.name.lower()} -- game in 4{suit.letter}"
            ),
        )


class GFMajors55(Rule):
    """Show 5-5 in the majors at game-forcing strength.

    1NT - 2H - 2S - 3H.  Transferred to spades, then bid 3H to show
    5+ hearts as well.  10+ HCP.  Opener chooses the better major fit.
    SAYC convention: transfer to spades first, then bid 3H = game-forcing 5-5.
    """

    @property
    def name(self) -> str:
        return "reresponse.gf_majors_55"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 344

    @property
    def prerequisites(self) -> Condition:
        return All(
            partner_opened_1nt,
            i_bid_transfer_1nt,
            partner_completed_transfer,
            transfer_is_spades,
        )

    @property
    def conditions(self) -> Condition:
        return All(
            HcpRange(min_hcp=10),
            SuitLength(Suit.HEARTS, min_len=5),
            SuitLength(Suit.SPADES, min_len=5),
        )

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.HEARTS)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(3, Suit.HEARTS),
            rule_name=self.name,
            explanation="10+ HCP, 5-5 in majors -- game-forcing, showing both",
            forcing=True,
        )


# ── Section F: After super-accept over 1NT ─────────────────────


class PassSuperAccept(Rule):
    """Pass after super-accept with a weak hand.

    1NT - 2D - 3H - Pass (or 1NT - 2H - 3S - Pass).
    0-7 HCP.  Already at the 3-level; partscore.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_super_accept"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 52

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_super_accepted)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=7)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation=f"Weak hand -- pass super-accept at 3{suit.letter}",
        )


class Game3NTSuperAccept(Rule):
    """Bid 3NT after super-accept with exactly 5 in transfer suit.

    1NT - 2D - 3H - 3NT (or 1NT - 2H - 3S - 3NT).
    8-15 HCP, exactly 5 cards.  Choice of game: opener can pass 3NT
    or correct to 4M with the known 4-card support.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_super_accept"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 336

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_super_accepted)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=15), _transfer_suit_5_exact)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                f"8-15 HCP, 5-card {suit.name.lower()} -- "
                f"3NT choice of game after super-accept"
            ),
        )


class Game4MSuperAccept(Rule):
    """Bid game in the transfer major after super-accept with 6+ cards.

    1NT - 2D - 3H - 4H (or 1NT - 2H - 3S - 4S).
    8-15 HCP, 6+ cards.  With 10+ card fit, the major game is clear.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_4m_super_accept"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 346

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_super_accepted)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=8, max_hcp=15), _transfer_suit_6_plus)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        suit = transfer_suit(ctx)
        return frozenset({SuitBid(4, suit)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"8-15 HCP, 6+ {suit.name.lower()} -- "
                f"game in 4{suit.letter} after super-accept"
            ),
        )


class Quant4NTSuperAccept(Rule):
    """Quantitative 4NT after super-accept with slam interest.

    1NT - 2D - 3H - 4NT (or 1NT - 2H - 3S - 4NT).
    16+ HCP.  Invites slam -- opener bids 6M or 6NT with maximum.
    """

    @property
    def name(self) -> str:
        return "reresponse.quant_4nt_super_accept"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 450

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_1nt, i_bid_transfer_1nt, partner_super_accepted)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=16)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                "16+ HCP after super-accept -- quantitative 4NT, inviting slam"
            ),
        )


# ── Section G: After transfer completion over 2NT ──────────────


class PassTransfer2NTSignoff(Rule):
    """Pass after transfer completion over 2NT with a very weak hand.

    2NT - 3D - 3H - Pass (or 2NT - 3H - 3S - Pass).
    0-3 HCP.  Sign-off at the 3-level.
    """

    @property
    def name(self) -> str:
        return "reresponse.pass_transfer_2nt_signoff"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 51

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_transfer_2nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return HcpRange(max_hcp=3)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[PassBid]:
        return frozenset({PASS})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=PASS,
            rule_name=self.name,
            explanation=(
                f"Weak hand -- sign-off in 3{suit.letter} after transfer over 2NT"
            ),
        )


class Game3NTTransfer2NT(Rule):
    """Bid 3NT after transfer completion over 2NT (5-card suit).

    2NT - 3D - 3H - 3NT (or 2NT - 3H - 3S - 3NT).
    4-11 HCP, exactly 5 cards.  Opener may correct to 4M with 3+ support.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_3nt_transfer_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 334

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_transfer_2nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=4, max_hcp=11), _transfer_suit_5_exact)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(3, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(3, Suit.NOTRUMP),
            rule_name=self.name,
            explanation=(
                f"4-11 HCP, 5-card {suit.name.lower()} over 2NT -- "
                f"3NT (opener may correct to 4{suit.letter})"
            ),
        )


class Game4MTransfer2NT(Rule):
    """Raise the transfer suit to game over 2NT.

    2NT - 3D - 3H - 4H (or 2NT - 3H - 3S - 4S).
    4-11 HCP, 6+ cards.  Game sign-off.
    """

    @property
    def name(self) -> str:
        return "reresponse.game_4m_transfer_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 348

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_transfer_2nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(min_hcp=4, max_hcp=11), _transfer_suit_6_plus)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        suit = transfer_suit(ctx)
        return frozenset({SuitBid(4, suit)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = transfer_suit(ctx)
        return RuleResult(
            bid=SuitBid(4, suit),
            rule_name=self.name,
            explanation=(
                f"4-11 HCP, 6+ {suit.name.lower()} over 2NT -- game in 4{suit.letter}"
            ),
        )


class Quant4NTTransfer2NT(Rule):
    """Quantitative 4NT after transfer completion over 2NT.

    2NT - 3D - 3H - 4NT (or 2NT - 3H - 3S - 4NT).
    12-13 HCP.  Invites 6NT or 6M.
    """

    @property
    def name(self) -> str:
        return "reresponse.quant_4nt_transfer_2nt"

    @property
    def category(self) -> Category:
        return Category.REBID_RESPONDER

    @property
    def priority(self) -> int:
        return 448

    @property
    def prerequisites(self) -> Condition:
        return All(partner_opened_2nt, i_bid_transfer_2nt, partner_completed_transfer)

    @property
    def conditions(self) -> Condition:
        return HcpRange(min_hcp=12, max_hcp=13)

    def possible_bids(self, ctx: AuctionContext) -> frozenset[SuitBid]:
        return frozenset({SuitBid(4, Suit.NOTRUMP)})

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=SuitBid(4, Suit.NOTRUMP),
            rule_name=self.name,
            explanation="12-13 HCP over 2NT -- quantitative 4NT, inviting slam",
        )
