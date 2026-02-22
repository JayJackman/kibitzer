# Phase 6: Opener's Rebids (COMPLETE)

**Status: Complete.** 30 rebid rules covering 5 response types. Remaining gaps (Jacoby 2NT, jump shift, etc.) are covered in [phase7-complete-suit-pipeline.md](phase7-complete-suit-pipeline.md).

## Context

Phases 1–5 are complete: domain model, hand evaluation, rule engine, opening bids, and responses to 1-of-a-suit openings. The natural next step is the opener's second bid — what opener does after hearing partner's response.

This is `Category.REBID_OPENER`. Phase detection already handles it: when the current player made the opening bid and partner has responded, `detect_phase()` returns `REBID_OPENER`.

All rules must be accurate to the ACBL SAYC System Booklet (SP-3, revised January 2006). The reference material lives in `research/03-rebids.md`.

## Scope

**In scope:** Opener's rebids after opening 1H, 1S, 1C, or 1D and receiving an uncontested response.

Response types handled:
- After single raise (1M→2M, 1m→2m)
- After limit raise (1M→3M, 1m→3m)
- After 1NT response
- After new suit at 1-level (e.g., 1D→1H, 1H→1S)
- After 2-over-1 new suit (e.g., 1H→2C, 1S→2D)

**Out of scope (Phase 7+):**
- After Jacoby 2NT (convention-specific sequence)
- After jump shift by responder (slam-level, rare)
- After game-level responses (3NT over major, 4M preemptive, 2NT/3NT over minor) — opener usually passes; slam exploration is Phase 7+
- Responder's rebids (`Category.REBID_RESPONDER`)
- Responses to 1NT/2NT openings (Stayman, transfers — conventions)
- Responses to 2C, weak twos, preempts
- Competitive bidding
- Help suit game tries (opener bids new suit after single raise to ask responder about a specific suit; requires both opener and responder rebid rules)

## Files

| File | Action |
|------|--------|
| `src/bridge/evaluate/hand_eval.py` | Update — add `bergen_points` |
| `src/bridge/evaluate/__init__.py` | Update — re-export `bergen_points` |
| `src/bridge/engine/rules/sayc/rebid/__init__.py` | Create — re-exports |
| `src/bridge/engine/rules/sayc/rebid/suit.py` | Create — rebid rules after 1-of-a-suit opening |
| `src/bridge/engine/rules/sayc/__init__.py` | Update — register rebid rules |
| `tests/evaluate/test_hand_eval.py` | Update — tests for `bergen_points` |
| `tests/engine/rules/sayc/rebid/__init__.py` | Create — empty |
| `tests/engine/rules/sayc/rebid/test_suit.py` | Create — unit tests |
| `tests/engine/test_sayc.py` | Update — add rebid integration tests |

## Helper Functions

### `bergen_points(hand, trump_suit) -> int` (in `hand_eval.py`)

Re-evaluates opener's hand strength after partner raises their suit. Once a trump fit is confirmed, shortness translates to ruffs and extra trumps/side-suit length provide additional trick-taking potential.

Formula (Marty Bergen, *Points Schmoints*):
1. Start with HCP
2. +2 for each singleton in a side suit
3. +4 for each void in a side suit
4. +1 for each trump beyond the 5th
5. +1 for any 4-card or 5-card side suit

This replaces `total_points` (HCP + length points) for all raise-related rebid decisions. For NT rebid decisions, continue using HCP only.

---

The rebid rules need to classify what response partner made. These are private helpers in `opener.py`:

### `_my_opening_bid(ctx) -> Bid`
Returns opener's first bid (`ctx.my_bids[0]`).

### `_my_opening_suit(ctx) -> Suit`
Returns the suit opener bid (never NOTRUMP for 1-suit openings).

### `_partner_response(ctx) -> Bid`
Returns partner's response (`ctx.partner_last_bid`).

### Response classifiers

```python
def _partner_raised(ctx) -> bool:
    """Partner raised our suit (any level)."""
    return _partner_response(ctx).suit == _my_opening_suit(ctx)

def _partner_single_raised(ctx) -> bool:
    """Partner made a single raise (1M→2M or 1m→2m)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 1

def _partner_limit_raised(ctx) -> bool:
    """Partner made a limit raise (1M→3M or 1m→3m)."""
    resp = _partner_response(ctx)
    opening = _my_opening_bid(ctx)
    return resp.suit == opening.suit and resp.level == opening.level + 2

def _partner_bid_1nt(ctx) -> bool:
    resp = _partner_response(ctx)
    return resp.suit == Suit.NOTRUMP and resp.level == 1

def _partner_bid_new_suit(ctx) -> bool:
    """Partner bid a new suit (not a raise, not NT)."""
    resp = _partner_response(ctx)
    return (resp.suit != _my_opening_suit(ctx)
            and resp.suit != Suit.NOTRUMP
            and resp.bid_type == BidType.SUIT)

def _partner_bid_new_suit_1_level(ctx) -> bool:
    return _partner_bid_new_suit(ctx) and _partner_response(ctx).level == 1

def _partner_bid_2_over_1(ctx) -> bool:
    return _partner_bid_new_suit(ctx) and _partner_response(ctx).level == 2
```

### Rebid suit-finding helpers

```python
def _find_rebid_suit(ctx) -> Suit | None:
    """Find a 6+ card suit to rebid (same as opening suit)."""
    suit = _my_opening_suit(ctx)
    if ctx.hand.suit_length(suit) >= 6:
        return suit
    return None

def _find_new_suit(ctx, *, max_level: int = 4) -> Suit | None:
    """Find a 4+ card second suit to bid, cheapest first.

    For reverses (new suit above opening suit at 2-level), caller checks
    strength requirements separately.
    """
    ...

def _is_reverse(ctx, new_suit: Suit) -> bool:
    """Whether bidding new_suit at the 2-level is a reverse.

    A reverse occurs when the new suit ranks higher than the opening suit
    and must be bid at the 2-level, forcing responder to the 3-level to
    return to opener's first suit.
    """
    opening_suit = _my_opening_suit(ctx)
    return new_suit > opening_suit
```

## Rules — After Single Raise of Major

Partner opened 1H/1S, responder raised to 2H/2S (3+ support, 6–10 support points).

Opener re-evaluates using **Bergen points** (HCP + shortness + extra trumps + side suit length). A fit is confirmed, so shortness now translates to ruffs. See `research/00-overview.md` for the full Bergen formula.

- 26+ combined → game (responder shows ~8 support pts on average)
- Opener's Bergen points: 12–15 → pass, 16–18 → invite, 19+ → game

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 300 | `rebid.game_after_raise_major` | 19+ bergen pts | 4M |
| 220 | `rebid.invite_after_raise_major` | 16–18 bergen pts | 3M |
| 60 | `rebid.pass_after_raise` | ≤15 bergen pts | Pass |

### `rebid.game_after_raise_major`

**SAYC**: "19+ points opposite a single raise; enough for game."

```
applies:
  - Partner single-raised my major
  - bergen_pts >= 19
select:
  - Bid 4 of my major
```

### `rebid.invite_after_raise_major`

**SAYC**: "16–18 points; invitational. Raise to 3."

```
applies:
  - Partner single-raised my major
  - 16 <= bergen_pts <= 18
select:
  - Bid 3 of my major
```

### `rebid.pass_after_raise`

Shared between major and minor raises. Minimum opener, content with partscore.

```
applies:
  - Partner single-raised my suit
  - bergen_pts <= 15
select:
  - Pass
```

## Rules — After Limit Raise of Major

Partner opened 1H/1S, responder jumped to 3H/3S (3+ support, 10–12 support points). Invitational — opener accepts or declines.

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 310 | `rebid.accept_limit_raise_major` | 15+ bergen pts | 4M |
| 70 | `rebid.decline_limit_raise` | ≤14 bergen pts | Pass |

### `rebid.accept_limit_raise_major`

**SAYC**: "Accept the invitation; bid game."

With responder showing ~11 support points, opener needs ~15 Bergen pts to reach 26 combined.

```
applies:
  - Partner limit-raised my major
  - bergen_pts >= 15
select:
  - Bid 4 of my major
```

### `rebid.decline_limit_raise`

Shared between major and minor. Decline the invitation.

```
applies:
  - Partner limit-raised my suit
  - bergen_pts <= 14
select:
  - Pass
```

## Rules — After Raise of Minor

Partner opened 1C/1D, responder raised to 2C/2D (6–10 HCP) or jumped to 3C/3D (10–12 HCP).

After a minor raise, the primary goal is usually 3NT rather than 5 of a minor. Opener with a balanced hand bids NT; with an unbalanced minimum, passes.

### After single raise of minor

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 320 | `rebid.3nt_after_raise_minor` | 18–19 HCP, balanced | 3NT |
| 210 | `rebid.2nt_after_raise_minor` | 12–14 HCP, balanced | 2NT |
| 170 | `rebid.new_suit_after_raise_minor` | 4+ new suit, 15+ bergen pts, unbalanced | New suit |
| 60 | `rebid.pass_after_raise` | Minimum bergen pts, no game interest | Pass |

### After limit raise of minor

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 330 | `rebid.3nt_after_limit_raise_minor` | 12+ HCP, balanced | 3NT |
| 180 | `rebid.5m_after_limit_raise_minor` | 15+ bergen pts, unbalanced, 6+ in minor | 5m |
| 70 | `rebid.decline_limit_raise` | ≤14 bergen pts, unbalanced | Pass |

### `rebid.3nt_after_raise_minor`

**SAYC**: After a single raise, opener with 18–19 HCP balanced bids 3NT. After a limit raise, 12+ balanced is enough.

```
applies:
  - Partner raised my minor (single or limit)
  - is_balanced or is_semi_balanced
  - HCP threshold: 18 for single raise, 12 for limit raise
select:
  - Bid 3NT
```

Note: could be one rule class with the HCP threshold varying by raise level, or two separate classes.

### `rebid.2nt_after_raise_minor`

```
applies:
  - Partner single-raised my minor
  - 12 <= HCP <= 14
  - is_balanced
select:
  - Bid 2NT
```

Shows the same hand that would have rebid 1NT (12–14 balanced) but over the raise, bids 2NT to show the balanced minimum.

## Rules — After 1NT Response

Partner opened 1-of-a-suit, responder bid 1NT (6–10 HCP, denies fit and higher suit).

Opener knows responder has a limited hand (6–10). Rebid choices:

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 360 | `rebid.3nt_over_1nt` | 19–21 HCP, balanced | 3NT |
| 340 | `rebid.jump_shift_over_1nt` | 19+ total pts, 4+ new suit | Jump in new suit |
| 250 | `rebid.2nt_over_1nt` | 18–19 HCP, balanced | 2NT |
| 230 | `rebid.jump_rebid_over_1nt` | 6+ in opening suit, 17–18 total pts | 3 of own suit |
| 150 | `rebid.new_lower_suit_over_1nt` | 4+ cards, new suit lower-ranking | 2 of new suit |
| 130 | `rebid.rebid_suit_over_1nt` | 6+ in opening suit, minimum | 2 of own suit |
| 50 | `rebid.pass_over_1nt` | Balanced minimum, 5-card suit | Pass |

### `rebid.3nt_over_1nt`

**SAYC**: "19–21 HCP, balanced."

```
applies:
  - Partner responded 1NT
  - 19 <= HCP <= 21
  - is_balanced or is_semi_balanced
select:
  - Bid 3NT
```

### `rebid.jump_shift_over_1nt`

**SAYC**: "Jump in new suit; 19+ points, 4+ cards; forcing."

```
applies:
  - Partner responded 1NT
  - total_pts >= 19
  - Has a 4+ card second suit
  - Not balanced (balanced hands bid NT)
select:
  - Jump in new suit (one level above cheapest available)
```

### `rebid.2nt_over_1nt`

**SAYC**: "18–19 HCP, balanced; invitational."

```
applies:
  - Partner responded 1NT
  - 18 <= HCP <= 19
  - is_balanced or is_semi_balanced
select:
  - Bid 2NT
```

### `rebid.jump_rebid_over_1nt`

**SAYC**: "6+ card suit, 17–18 points; invitational."

```
applies:
  - Partner responded 1NT
  - 6+ cards in opening suit
  - 17 <= total_pts <= 18
select:
  - Bid 3 of opening suit
```

### `rebid.new_lower_suit_over_1nt`

**SAYC**: "2 of a lower new suit; 4+ cards; non-forcing."

A "lower" suit is one that can be bid at the 2-level without going past opener's suit. For example, after opening 1H: 2C and 2D are valid new suits. After opening 1S: 2C, 2D, 2H are valid. After opening 1D: only 2C. After opening 1C: nothing lower exists.

```
applies:
  - Partner responded 1NT
  - Has a 4+ card suit biddable at the 2-level below opening suit
  - Not strong enough for a jump (total_pts <= 18)
select:
  - Bid 2 of the new suit (cheapest 4+ card suit)
```

### `rebid.rebid_suit_over_1nt`

**SAYC**: "2 of original suit; 6+ cards; non-forcing."

```
applies:
  - Partner responded 1NT
  - 6+ cards in opening suit
  - Minimum (total_pts <= 16)
select:
  - Bid 2 of opening suit
```

### `rebid.pass_over_1nt`

**SAYC**: "Balanced minimum; pass."

Pass when opener has a balanced minimum (12–14) with only a 5-card suit and no second suit. The 1NT contract is as good as anything.

```
applies:
  - Partner responded 1NT
  - Minimum balanced hand (no 6-card suit, no second suit)
select:
  - Pass
```

## Rules — After New Suit at 1-Level

Partner opened 1-of-a-suit, responder bid a new suit at the 1-level (e.g., 1C→1H, 1D→1S, 1H→1S). Responder shows 4+ cards and 6+ HCP, forcing one round.

This is the most complex rebid scenario because opener has the full range of minimum/medium/maximum actions.

### Minimum (12–16 total points)

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 160 | `rebid.raise_responder` | 4-card support, 12–16 total pts | Raise to 2 of responder's suit |
| 140 | `rebid.new_suit_nonreverse` | 4+ cards, new suit, non-reverse | Bid new suit at cheapest level |
| 120 | `rebid.rebid_own_suit` | 6+ in opening suit, minimum | 2 of own suit |
| 100 | `rebid.1nt` | 12–14 HCP, balanced | 1NT |

### Medium (17–18 total points)

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 280 | `rebid.jump_raise_responder` | 4-card support, 17–18 total pts | 3 of responder's suit |
| 260 | `rebid.reverse` | 4+ in new higher-ranking suit, 17+ total pts, first suit longer | New suit (reverse) |
| 240 | `rebid.jump_rebid_own_suit` | 6+ in opening suit, 17–18 total pts | 3 of own suit |

### Maximum (19–21 total points)

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 380 | `rebid.jump_to_2nt` | 18–19 HCP, balanced | 2NT |
| 370 | `rebid.jump_shift_new_suit` | 19+ total pts, 4+ in second suit | Jump in new suit |

### `rebid.raise_responder`

**SAYC**: "Raise responder's suit at cheapest level — 4-card support, minimum."

```
applies:
  - Partner bid a new suit at 1-level
  - 4+ cards in responder's suit
  - 12 <= total_pts <= 16
select:
  - Bid 2 of responder's suit
```

### `rebid.new_suit_nonreverse`

**SAYC**: "Bid new suit at cheapest level — 4+ cards, new suit ranks lower than first suit (non-reverse). Minimum."

A non-reverse is when the new suit can be bid at the 1-level, or at the 2-level but ranking lower than the opening suit (so responder can return to opener's suit at the same level).

```
applies:
  - Partner bid a new suit at 1-level
  - Has 4+ card second suit
  - Not a reverse (new suit lower than opening suit, or at 1-level)
  - total_pts <= 18
select:
  - Bid new suit at cheapest level
```

### `rebid.rebid_own_suit`

**SAYC**: "Rebid own suit at cheapest level — 6+ cards, minimum."

```
applies:
  - Partner bid a new suit at 1-level (or 2-over-1)
  - 6+ cards in opening suit
  - Minimum (12–16 total pts)
select:
  - Bid 2 of opening suit
```

### `rebid.1nt`

**SAYC**: "12–14 HCP, balanced, no other descriptive bid."

```
applies:
  - Partner bid a new suit at 1-level
  - 12 <= HCP <= 14
  - is_balanced
select:
  - Bid 1NT
```

### `rebid.reverse`

**SAYC**: "New suit ranking higher than first suit at the 2-level — requires 17+ points. First suit must be longer than second."

Example: 1D→1S→2H is a reverse (hearts rank higher than diamonds). It forces responder to the 3-level to return to diamonds.

```
applies:
  - Partner bid a new suit at 1-level
  - Has 4+ card suit that ranks higher than opening suit
  - Opening suit longer than new suit
  - total_pts >= 17
select:
  - Bid 2 of the higher-ranking suit
```

### `rebid.jump_raise_responder`

**SAYC**: "Jump raise responder's suit — 4-card support, 17–18 points."

```
applies:
  - Partner bid a new suit at 1-level
  - 4+ cards in responder's suit
  - 17 <= total_pts <= 18
select:
  - Bid 3 of responder's suit
```

### `rebid.jump_rebid_own_suit`

**SAYC**: "Jump rebid own suit — 6+ cards, 17–18 points."

```
applies:
  - Partner bid a new suit at 1-level
  - 6+ cards in opening suit
  - 17 <= total_pts <= 18
select:
  - Bid 3 of opening suit
```

### `rebid.jump_to_2nt`

**SAYC**: "Jump to 2NT — 18–19 HCP, balanced."

```
applies:
  - Partner bid a new suit at 1-level
  - 18 <= HCP <= 19
  - is_balanced or is_semi_balanced
select:
  - Bid 2NT
```

### `rebid.jump_shift_new_suit`

**SAYC**: "Jump shift into second suit — 19+ points, 4+ cards; forcing."

```
applies:
  - Partner bid a new suit at 1-level
  - total_pts >= 19
  - Has a 4+ card second suit
  - Not balanced (balanced hands jump to 2NT or 3NT)
select:
  - Jump in new suit
```

## Rules — After 2-Over-1 Response

Partner opened 1M, responder bid a new suit at the 2-level (e.g., 1H→2C, 1S→2D). Responder shows 4+ cards and 10+ HCP, forcing one round with a promise to rebid.

Since responder has already promised 10+, opener can rebid more naturally — even minimum rebids keep the auction alive because responder will bid again.

| Priority | Rule | Condition | Bid |
|----------|------|-----------|-----|
| 290 | `rebid.raise_2over1_responder` | 4-card support | 3 of responder's suit |
| 270 | `rebid.new_suit_after_2over1` | 4+ in third suit | New suit |
| 190 | `rebid.rebid_suit_after_2over1` | 6+ in opening suit | 2 of own suit (or 3 if jump) |
| 110 | `rebid.nt_after_2over1` | Balanced, no other descriptive bid | 2NT (12–14) or 3NT (18–19) |

### `rebid.raise_2over1_responder`

```
applies:
  - Partner bid a new suit at 2-level (2-over-1)
  - 4+ cards in responder's suit
select:
  - Bid 3 of responder's suit
```

### `rebid.new_suit_after_2over1`

```
applies:
  - Partner bid a new suit at 2-level
  - 4+ cards in a third suit (not opening suit, not responder's suit)
select:
  - Bid cheapest available third suit
```

### `rebid.rebid_suit_after_2over1`

```
applies:
  - Partner bid a new suit at 2-level
  - 6+ cards in opening suit
select:
  - Bid cheapest level of opening suit (usually 2 of own suit)
```

### `rebid.nt_after_2over1`

```
applies:
  - Partner bid a new suit at 2-level
  - Balanced
  - No 4-card support for responder, no 6-card suit, no biddable third suit
select:
  - 2NT (12–14 HCP) or 3NT (18–19 HCP)
```

Note: the level depends on HCP. This could be two separate rules or one rule with conditional level. Two separate rules (split at 15 HCP) is cleaner.

## Priority Summary

All rules are in `Category.REBID_OPENER`. Priorities must be globally unique within the category.

| Range | Meaning |
|-------|---------|
| 350–390 | Maximum NT / jump shifts (game-forcing) |
| 300–340 | Game bids, accepting invitations |
| 250–290 | Medium-strength bids (invitational, 2-over-1 responses) |
| 200–240 | Invitational raises, minor NT bids |
| 100–190 | Minimum rebids |
| 50–70 | Pass / decline |

Full priority list (sorted descending):

| Priority | Rule Name |
|----------|-----------|
| 380 | rebid.jump_to_2nt |
| 370 | rebid.jump_shift_new_suit |
| 360 | rebid.3nt_over_1nt |
| 340 | rebid.jump_shift_over_1nt |
| 330 | rebid.3nt_after_limit_raise_minor |
| 320 | rebid.3nt_after_raise_minor |
| 310 | rebid.accept_limit_raise_major |
| 300 | rebid.game_after_raise_major |
| 290 | rebid.raise_2over1_responder |
| 280 | rebid.jump_raise_responder |
| 270 | rebid.new_suit_after_2over1 |
| 260 | rebid.reverse |
| 250 | rebid.2nt_over_1nt |
| 240 | rebid.jump_rebid_own_suit |
| 230 | rebid.jump_rebid_over_1nt |
| 220 | rebid.invite_after_raise_major |
| 210 | rebid.2nt_after_raise_minor |
| 200 | rebid.nt_after_2over1_max |
| 190 | rebid.rebid_suit_after_2over1 |
| 180 | rebid.5m_after_limit_raise_minor |
| 170 | rebid.new_suit_after_raise_minor |
| 160 | rebid.raise_responder |
| 150 | rebid.new_lower_suit_over_1nt |
| 140 | rebid.new_suit_nonreverse |
| 130 | rebid.rebid_suit_over_1nt |
| 120 | rebid.rebid_own_suit |
| 110 | rebid.nt_after_2over1_min |
| 100 | rebid.1nt |
| 70 | rebid.decline_limit_raise |
| 60 | rebid.pass_after_raise |
| 50 | rebid.pass_over_1nt |

~31 rules. Rules from different response types never overlap (a response is exactly one type), so cross-group priority ordering is only relevant for registry uniqueness.

## Testing Strategy

### Test Context Helper

```python
def _ctx(pbn: str, opening: str, response: str) -> BiddingContext:
    """Build a BiddingContext where opener rebids after a response."""
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))   # N opens
    auction.add_bid(Bid.make_pass())      # E passes
    auction.add_bid(parse_bid(response))  # S responds
    auction.add_bid(Bid.make_pass())      # W passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.NORTH, auction=auction)
    )
```

### Test Hands — After Single Raise of Major

| Opener's Hand (PBN) | HCP | Bergen Pts | Opening | Response | Expected | SAYC Rule |
|----------------------|-----|------------|---------|----------|----------|-----------|
| `AKJ52.KQ3.84.A73` | 17 | 17 | 1S | 2S | 3S (invite) | 16–18, raise to 3 |
| `AKJ52.A3.K84.A73` | 19 | 19 | 1S | 2S | 4S (game) | 19+ bergen |
| `AKJ82.A3.8.AK732` | 17 | 21 | 1S | 2S | 4S (game) | 19+ bergen (singleton +2, side 5-card +1, extra trump +1) |
| `KJ852.KQ3.84.A73` | 14 | 14 | 1S | 2S | Pass | ≤15, content |

Note: Bergen points add value for shortness and extra length once a fit is confirmed. Exact hands to be finalized during implementation.

### Test Hands — After Limit Raise of Major

| Opener's Hand | HCP | Bergen Pts | Opening | Response | Expected | SAYC Rule |
|---------------|-----|------------|---------|----------|----------|-----------|
| `AKJ52.KQ3.84.A73` | 17 | 17 | 1S | 3S | 4S (accept) | 15+ bergen, bid game |
| `KJ852.A3.8.AK732` | 15 | 18 | 1S | 3S | 4S (accept) | 15+ bergen (singleton +2, 5-card side suit +1) |
| `KJ852.Q73.84.A73` | 10 | 10 | 1S | 3S | Pass | ≤14 bergen, decline |

Note: exact Bergen point calculations to be verified during implementation.

### Test Hands — After 1NT Response

| Opener's Hand | HCP | Total Pts | Opening | Response | Expected | SAYC Rule |
|---------------|-----|-----------|---------|----------|----------|-----------|
| `AKJ52.KQ3.84.A73` | 17 | 18 | 1S | 1NT | 2NT | 18–19 balanced, invitational |
| `AKJ952.KQ3.84.A7` | 17 | 18 | 1S | 1NT | 3S | 6+ suit, 17–18, invitational |
| `AKJ52.K3.84.AK73` | 18 | 19 | 1S | 1NT | 2NT | 18–19 balanced |
| `KJ852.KQ3.84.A73` | 14 | 15 | 1S | 1NT | Pass | Balanced minimum |
| `AKQJ52.K3.84.A73` | 17 | 19 | 1S | 1NT | 3S | 6+ suit, 17–18 |
| `KJ8532.KQ3.8.A73` | 13 | 15 | 1S | 1NT | 2S | 6+ suit, minimum |
| `KJ852.KQ3.84.AQ3` | 15 | 16 | 1S | 1NT | 2C | New lower suit, 4+ |

### Test Hands — After New Suit at 1-Level

| Opener's Hand | HCP | Total Pts | Opening | Response | Expected | SAYC Rule |
|---------------|-----|-----------|---------|----------|----------|-----------|
| `84.AKJ52.KQ3.A73` | 17 | 18 | 1H | 1S | 2NT | 18–19 balanced (wait — 2-4-3-3 is not balanced with doubleton) |
| `A4.KJ852.KQ3.Q73` | 14 | 15 | 1H | 1S | 1NT | 12–14 balanced |
| `K4.AKJ52.Q73.A73` | 16 | 17 | 1H | 1S | 2H | Rebid 6+ (wait — only 5 hearts) |
| `K4.AKJ852.Q7.A73` | 16 | 18 | 1H | 1S | 3H | Jump rebid, 6+ suit, 17–18 |
| `K842.AKJ52.Q7.A3` | 16 | 17 | 1H | 1S | 2S | Raise responder, 4-card support |
| `K842.AKJ52.Q7.AK` | 18 | 19 | 1H | 1S | 3S | Jump raise, 4-card support, 17–18 |
| `K4.AKJ52.AQ73.73` | 15 | 16 | 1H | 1S | 2D | New suit non-reverse |
| `K4.AQ852.73.AKQ3` | 17 | 18 | 1H | 1S | 2D→err | Actually 2C is non-reverse... |

Note: test hands need careful construction. The exact hands will be finalized during implementation to ensure they match the conditions cleanly.

### Test Hands — After 2-Over-1

| Opener's Hand | Opening | Response | Expected | SAYC Rule |
|---------------|---------|----------|----------|-----------|
| `A4.AKJ52.Q73.K73` | 1H | 2C | 2H | Rebid own suit, 6+ (wait — only 5H) |
| `A4.AKJ852.Q7.K73` | 1H | 2C | 2H | Rebid 6+ suit |
| `AK42.AKJ52.Q7.73` | 1H | 2D | 2S | New suit (third suit) |
| `A4.AKJ52.Q73.K73` | 1H | 2C | 2NT | Balanced, no fit, no 6 |

### Integration Tests (in `test_sayc.py`)

Full pipeline tests that verify `REBID_OPENER` rules are detected and selected correctly:

```python
def test_invite_after_raise():
    """Opener with 17 pts rebids 3S after 1S→2S."""
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid("1S"))   # N opens
    auction.add_bid(parse_bid("P"))    # E
    auction.add_bid(parse_bid("2S"))   # S raises
    auction.add_bid(parse_bid("P"))    # W
    # N rebids with 17 bergen pts
    ...
    assert result.rule_name == "rebid.invite_after_raise_major"
```

## Implementation Order

1. `bergen_points` in `hand_eval.py` + tests — needed by raise rules
2. Helper functions in `opener.py`
3. After single raise of major (3 rules) — simplest, validates Bergen integration
4. After limit raise of major (2 rules)
5. After raise of minor (4–5 rules)
6. After 1NT response (7 rules)
7. After new suit at 1-level (9 rules) — most complex
8. After 2-over-1 (4 rules)
9. Register all rules in `sayc/__init__.py`
10. Unit tests for each group
11. Integration tests in `test_sayc.py`
12. `pdm run check`

## Verification

```bash
pdm run test tests/engine/rules/sayc/rebid/
pdm run test tests/engine/test_sayc.py
pdm run check
```

## Open Questions

1. ~~**Total points vs. HCP for re-evaluation**~~ **Resolved**: Use `bergen_points(hand, trump_suit)` for all raise-related rebid decisions. Bergen points (Marty Bergen, *Points Schmoints*) are specifically designed for opener's re-evaluation after partner raises. They replace `total_pts` once a fit is confirmed. HCP is still used for NT rebid decisions.

2. **Game try bids (help suit)**: After a single raise, opener can bid a new suit as a "help suit game try" instead of just raising to 3. This is a more advanced concept where opener asks responder about a specific suit. Deferred to Phase 7+ — the simple "raise to 3 as invitation" is the standard approach and covers the most common case. Requires opener-side rules (bid help suit instead of raising to 3) and responder-side rules (evaluate holding in partner's suit and decide game vs sign-off).

3. **Minor raise rebid specifics**: The SAYC booklet is less prescriptive about rebids after minor raises than major raises. The rules above follow general principles (try for 3NT with balanced, pass with minimum unbalanced). The exact HCP thresholds may need adjustment during testing.

4. **New suit selection after 1NT**: When opener bids a new lower suit over 1NT, should they bid the cheapest 4-card suit or the longest? SAYC says "4+ cards, non-forcing" without specifying. The implementation will bid the longest, with the cheapest as tiebreaker.

5. **Reverse guarantees**: A reverse promises the first suit is strictly longer than the second (`>`, not `>=`). Equal-length suits can't produce a reverse because you would have opened the higher-ranking suit. The `suit_length(opening_suit) > suit_length(new_suit)` check is a safety net that validates this invariant.
