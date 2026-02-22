# Phase 5: Responses to 1-of-a-Major and 1-of-a-Minor

## Context

Phases 1–4 are complete: domain model, hand evaluation, rule engine skeleton, and opening bid rules. Phase 5 implements the first response rules — how responder bids after partner opens 1H, 1S, 1C, or 1D, with no interference from opponents.

This is the natural next step because 1-suit openings are the most common and their responses are the most thoroughly codified in SAYC. Responses to NT openings (Stayman, Jacoby transfers) and to 2C/weak twos are deferred to Phase 6 — they involve conventions with multi-round sequences that add significant complexity.

All rules must be accurate to the ACBL SAYC System Booklet (SP-3, revised January 2006). The reference material lives in `research/02-responses.md`.

**Phase detection is already wired:** `BidSelector.detect_phase()` returns `Category.RESPONSE` when partner opened and it's responder's first non-pass bid with no interference.

## Scope

**In scope:** Responses to 1H, 1S, 1C, 1D (uncontested — `Category.RESPONSE`).

**Out of scope (Phase 6+):**
- Responses to 1NT/2NT (Stayman, Jacoby transfers, quantitative)
- Responses to 2C (waiting 2D, positive responses)
- Responses to weak twos / preempts
- Competitive responses (`Category.COMPETITIVE_RESPONSE`)
- Opener's rebids (`Category.REBID_OPENER`)

## Files

| File | Action |
|------|--------|
| `src/bridge/evaluate/hand_eval.py` | Update — add `support_points` |
| `src/bridge/evaluate/__init__.py` | Update — re-export `support_points` |
| `src/bridge/engine/rules/sayc/response/__init__.py` | Create — re-exports |
| `src/bridge/engine/rules/sayc/response/major.py` | Create — responses to 1H/1S |
| `src/bridge/engine/rules/sayc/response/minor.py` | Create — responses to 1C/1D |
| `src/bridge/engine/rules/sayc/__init__.py` | Update — register response rules |
| `tests/engine/rules/sayc/response/__init__.py` | Create — empty |
| `tests/engine/rules/sayc/response/test_major.py` | Create |
| `tests/engine/rules/sayc/response/test_minor.py` | Create |
| `tests/engine/test_sayc.py` | Update — add response integration tests |
| `tests/evaluate/test_hand_eval.py` | Update — tests for `support_points` |

## Helper Functions

### `support_points(hand, trump_suit) -> int` in `hand_eval.py`

Dummy points for raising partner's suit: HCP + shortness in non-trump suits.

```
support_points(hand, trump_suit):
    return hcp(hand) + distribution_points(hand, trump_suit)
```

Note: `distribution_points(hand, trump_suit)` already exists and already excludes shortness in the trump suit. The new function is a thin convenience wrapper.

**SAYC shortness values** (already implemented in `distribution_points`): void=5, singleton=3, doubleton=1.

**Important:** Support points are only used when raising partner's suit (major raises). When responding with a new suit or 1NT, use HCP only.

## Response Rules — 1-of-a-Major (1H / 1S)

All responses require 6+ points. The `applies()` method for each rule must verify:
- Partner opened 1H or 1S (via `ctx.opening_bid`)
- Responder has adequate points
- No interference (`Category.RESPONSE` guarantees this)

### Priority Assignments

| Priority | Rule | SAYC Reference |
|----------|------|----------------|
| 380 | `response.jump_shift` | 19+ points, 4+ cards in new suit; slam invitational |
| 340 | `response.jacoby_2nt` | 4+ card support, 13+ support pts; game forcing |
| 320 | `response.game_raise_major` | 5+ card support, <10 HCP, singleton/void; preemptive |
| 300 | `response.3nt_over_major` | 15-17 HCP, balanced, exactly 2-card support; to play |
| 280 | `response.limit_raise_major` | 3+ card support, 10-12 support pts; invitational |
| 260 | `response.2_over_1` | 4+ cards in new suit, 10+ HCP; forcing one round |
| 240 | `response.new_suit_1_level` | 4+ cards, 6+ HCP; forcing one round (1H→1S) |
| 220 | `response.single_raise_major` | 3+ card support, 6-10 support pts |
| 200 | `response.1nt_over_major` | 6-10 HCP, denies 3+ support, denies 4S over 1H |
| 50 | `response.pass` | Fallback: <6 HCP |

### Priority Rationale

- **Jump shift (380)**: Strongest action — 19+ points must never be underbid.
- **Jacoby 2NT (340)**: Game-forcing raise with 4+ support — most descriptive game-force. Alerts required (conventional bid).
- **Game raise / 3NT (300-320)**: Game-level bids. Preemptive 4-major outranks 3NT because shape requirements are more specific.
- **Limit raise (280)**: Invitational with support — more specific than 2-over-1 because it confirms fit.
- **2-over-1 (260)**: New suit forcing at 2-level; higher than 1-level new suit because it promises more strength.
- **New suit at 1-level (240)**: 1H→1S — forcing, only 6+ needed. Above single raise because finding a spade fit is higher priority.
- **Single raise (220)**: 6-10 with 3+ support.
- **1NT (200)**: Dustbin — denies good options. Above pass but below everything else.
- **Pass (50)**: Fallback for <6 HCP.

### Rule Specifications

#### `response.jump_shift` — Jump Shift

**SAYC**: "19+ points, 4+ cards in new suit (5+ for minor jump shifts); slam invitational."

```
applies:
  - Partner opened 1H or 1S
  - HCP >= 19
  - Has a 4+ card suit to bid (not opener's suit)
select:
  - Jump one level in new suit (e.g., 1H→2S, 1H→3C, 1H→3D, 1S→3C, 1S→3D, 1S→3H)
  - forcing = True
```

Suit selection: bid the longest new suit; with equal length, bid the higher-ranking.

#### `response.jacoby_2nt` — Jacoby 2NT

**SAYC**: "4+ card support, 13+ dummy points; game forcing."

```
applies:
  - Partner opened 1H or 1S
  - 4+ cards in opener's major
  - support_points >= 13
select:
  - Bid 2NT
  - forcing = True
  - alerts = ("Jacoby 2NT — game forcing raise",)
```

#### `response.game_raise_major` — Preemptive Game Raise (4H / 4S)

**SAYC**: "5+ card support, singleton or void, fewer than 10 HCP."

```
applies:
  - Partner opened 1H or 1S
  - 5+ cards in opener's major
  - HCP < 10
  - Has a singleton or void in a side suit
select:
  - Bid 4 of opener's major
```

#### `response.3nt_over_major` — 3NT Over Major

**SAYC**: "15-17 HCP, balanced, exactly 2-card support; to play."

```
applies:
  - Partner opened 1H or 1S
  - 15 <= HCP <= 17
  - is_balanced
  - Exactly 2 cards in opener's major
select:
  - Bid 3NT
```

Note: This shows a specific hand type. With 13-14 balanced and 2-card support, responder bids a new suit and later bids NT.

#### `response.limit_raise_major` — Limit Raise (3H / 3S)

**SAYC**: "3+ card support, 10-12 dummy points; invitational."

```
applies:
  - Partner opened 1H or 1S
  - 3+ cards in opener's major
  - 10 <= support_points <= 12
select:
  - Bid 3 of opener's major
```

#### `response.2_over_1` — Two-Over-One in New Suit

**SAYC**: "4+ cards, 10+ points; forcing one round."

```
applies:
  - Partner opened 1H or 1S
  - HCP >= 10
  - Has a 4+ card suit biddable at 2-level (not opener's suit)
  - Not qualified for jump shift (HCP < 19)
select:
  - Bid 2 of the new suit (cheapest biddable suit up the line)
  - forcing = True
```

Suit selection: with multiple suits, bid the longest; with ties, bid the cheapest (up the line).

Over 1S: suits available at 2-level are 2C, 2D, 2H.
Over 1H: suits available at 2-level are 2C, 2D (2S would be at 1-level, not 2-over-1).

#### `response.new_suit_1_level` — New Suit at 1-Level (1H→1S)

**SAYC**: "4+ cards, 6+ points; forcing one round."

```
applies:
  - Partner opened 1H (not 1S — can't bid a new suit at 1-level over 1S)
  - 4+ spades
  - HCP >= 6
select:
  - Bid 1S
  - forcing = True
```

Note: Over 1H, the only 1-level new suit is 1S. Over 1S, there are no higher suits at the 1-level.

#### `response.single_raise_major` — Single Raise (2H / 2S)

**SAYC**: "3+ card support, 6-10 dummy points."

```
applies:
  - Partner opened 1H or 1S
  - 3+ cards in opener's major
  - 6 <= support_points <= 10
select:
  - Bid 2 of opener's major
```

#### `response.1nt_over_major` — 1NT Response

**SAYC**: "6-10 HCP; denies 3-card support for opener's major; denies 4 spades over 1H; non-forcing."

```
applies:
  - Partner opened 1H or 1S
  - 6 <= HCP <= 10
  - Fewer than 3 cards in opener's major
  - If opener bid 1H: denies 4+ spades
select:
  - Bid 1NT
  - forcing = False
```

#### `response.pass` — Pass

```
applies:
  - Partner opened (1-suit)
  - HCP < 6
select:
  - Pass
```

This is a shared fallback across all 1-suit responses.

## Response Rules — 1-of-a-Minor (1C / 1D)

All responses require 6+ points. Most rules overlap with major responses, but with key differences.

### Priority Assignments

| Priority | Rule | SAYC Reference |
|----------|------|----------------|
| 380 | `response.jump_shift` | Shared with major (same rule) |
| 310 | `response.3nt_over_minor` | 16-17 HCP, balanced, denies 4-card major |
| 290 | `response.2nt_over_minor` | 13-15 HCP, balanced, denies 4-card major; game forcing |
| 270 | `response.limit_raise_minor` | 10-12 pts, adequate trump support; invitational |
| 260 | `response.2_over_1` | Shared with major (same rule handles minor→minor too) |
| 250 | `response.new_suit_1_level` | Extended: now handles all 4-card suits up the line |
| 230 | `response.single_raise_minor` | 6-10 pts, adequate trump support |
| 210 | `response.1nt_over_minor` | 6-10 HCP, no 4-card major; non-forcing |
| 50 | `response.pass` | Shared fallback |

### Key Differences from Major Responses

1. **No Jacoby 2NT** — only applies over major openings.
2. **No preemptive game raise** — only applies to majors.
3. **No 3NT "balanced with 2-card support"** — the minor versions are different:
   - 2NT over minor = 13-15 HCP balanced, game forcing
   - 3NT over minor = 16-17 HCP balanced, to play
4. **Support requirements differ**: 1D raise needs 4+ diamonds, 1C raise needs 5+ clubs.
5. **New suit at 1-level priority**: With multiple 4-card suits, bid up the line (lowest first) to avoid missing a major fit.
6. **No support points for minor raises** — per SAYC, don't add shortness when raising a minor (the final contract may be notrump). Use HCP only.

### Rule Specifications

#### `response.new_suit_1_level` (extended for minors)

Over 1C: can bid 1D, 1H, or 1S with 4+ cards at 6+ HCP.
Over 1D: can bid 1H or 1S with 4+ cards at 6+ HCP.
Over 1H: can bid 1S with 4+ cards at 6+ HCP.

**SAYC priority**: "Show a 4-card major at the 1-level before raising." With multiple 4-card suits, bid up the line (cheapest first).

**Implementation**: This is a single `response.new_suit_1_level` rule class that handles both major and minor contexts. The `_find_suit()` helper iterates through available higher-ranking strains at the 1-level.

#### `response.2_over_1` (extended for minors)

Over 1D: can bid 2C with 4+ clubs and 10+ HCP.
Over 1C: can bid 2D with 4+ diamonds (but this is rarely done; usually 1D is available).

Note: 2-over-1 in a new suit over a minor is forcing one round (same as over a major).

#### `response.single_raise_minor` — Single Raise (2C / 2D)

**SAYC**: "Adequate trump support, 6-10 points."

```
applies:
  - Partner opened 1C or 1D
  - Adequate support (5+ for clubs, 4+ for diamonds)
  - 6 <= HCP <= 10
  - No biddable 4-card major at 1-level
select:
  - Bid 2 of opener's minor
```

#### `response.limit_raise_minor` — Jump Raise (3C / 3D)

**SAYC**: "Adequate trump support, 10-12 points; invitational."

```
applies:
  - Partner opened 1C or 1D
  - Adequate support (5+ for clubs, 4+ for diamonds)
  - 10 <= HCP <= 12
  - No biddable 4-card major at 1-level
select:
  - Bid 3 of opener's minor
```

#### `response.2nt_over_minor` — 2NT Over Minor

**SAYC**: "13-15 HCP, balanced, denies 4-card major; game forcing."

```
applies:
  - Partner opened 1C or 1D
  - 13 <= HCP <= 15
  - is_balanced
  - No 4-card major
select:
  - Bid 2NT
  - forcing = True
```

#### `response.3nt_over_minor` — 3NT Over Minor

**SAYC**: "16-17 HCP, balanced, denies 4-card major; to play."

```
applies:
  - Partner opened 1C or 1D
  - 16 <= HCP <= 17
  - is_balanced
  - No 4-card major
select:
  - Bid 3NT
```

#### `response.1nt_over_minor` — 1NT Over Minor

**SAYC**: "6-10 HCP, no 4-card major; non-forcing."

```
applies:
  - Partner opened 1C or 1D
  - 6 <= HCP <= 10
  - No 4-card major biddable at 1-level
select:
  - Bid 1NT
```

## Shared vs. Separate Rules

Several response rules apply to both major and minor openings. The approach:

| Rule | Scope | Notes |
|------|-------|-------|
| `response.jump_shift` | Both | Same logic, different suit selection |
| `response.new_suit_1_level` | Both | Available suits differ by opening |
| `response.2_over_1` | Both | Available suits differ by opening |
| `response.pass` | Both | Always applies when <6 HCP |
| `response.jacoby_2nt` | Major only | |
| `response.game_raise_major` | Major only | |
| `response.3nt_over_major` | Major only | |
| `response.limit_raise_major` | Major only | |
| `response.single_raise_major` | Major only | |
| `response.1nt_over_major` | Major only | |
| `response.2nt_over_minor` | Minor only | |
| `response.3nt_over_minor` | Minor only | |
| `response.limit_raise_minor` | Minor only | |
| `response.single_raise_minor` | Minor only | |
| `response.1nt_over_minor` | Minor only | |

Shared rules go in a separate file or in one of the two files with the `applies()` method checking which opening was made. **Decision: put shared rules in `major.py`** (where the concept originates) and have them check the opening bid type internally. This keeps the codebase simpler than a third `shared.py` file.

Actually, cleaner approach: **put shared rules in `major.py`** since they originated there, and `minor.py` only contains minor-specific rules (raises, NT responses). Each rule's `applies()` checks whether the opening was a major or minor.

## File Layout

```
src/bridge/engine/rules/sayc/response/
    __init__.py         → re-exports all response rule classes
    major.py            → Major-specific + shared rules (jump shift, new suit, 2-over-1, pass)
    minor.py            → Minor-specific rules (raises, NT)
```

## Testing Strategy

### Test Context Helper

```python
def _ctx(pbn: str, opening: str = "1H") -> BiddingContext:
    """Build a BiddingContext where partner opened and responder acts."""
    auction = AuctionState(dealer=Seat.NORTH)
    auction.add_bid(parse_bid(opening))  # Partner (N) opens
    auction.add_bid(Bid.make_pass())     # RHO (E) passes
    return BiddingContext(
        Board(hand=Hand.from_pbn(pbn), seat=Seat.SOUTH, auction=auction)
    )
```

### Test Hands — Responses to 1H

| Hand | HCP | Shape | Support Pts | Expected | SAYC Rule |
|------|-----|-------|-------------|----------|-----------|
| `AKQ93.84.AKJ3.A4` | 20 | 5-2-4-2 | — | 2S (jump shift) | 19+ pts, 5+ spades |
| `K842.AJ83.A4.K73` | 14 | 4-4-2-3 | 17 | 2NT (Jacoby) | 4+ support, 13+ support pts |
| `84.KJ842.4.98743` | 5 | 2-5-1-5 | — | 4H (preemptive) | 5+ support, singleton, <10 HCP |
| `AQ32.84.KQ84.AJ3` | 16 | 4-2-4-3 | — | 3NT | 15-17 balanced, 2-card support |
| `K84.QJ3.A842.973` | 10 | 3-3-4-3 | 11 | 3H (limit raise) | 3+ support, 10-12 support pts |
| `84.73.AKJ84.K973` | 11 | 2-2-5-4 | — | 2D (2-over-1) | 10+ HCP, 4+ new suit |
| `KQ84.73.J84.A973` | 9 | 4-2-3-4 | — | 1S | 4+ spades, 6+ HCP |
| `K84.QJ3.843.9732` | 6 | 3-3-3-4 | 7 | 2H (single raise) | 3+ support, 6-10 support pts |
| `K84.73.QJ84.9732` | 6 | 3-2-4-4 | — | 1NT | 6-10, <3 support, no 4S |
| `843.73.J842.9732` | 1 | 3-2-4-4 | — | Pass | <6 HCP |

### Test Hands — Responses to 1S

| Hand | HCP | Shape | Support Pts | Expected | SAYC Rule |
|------|-----|-------|-------------|----------|-----------|
| `AJ83.K842.A4.K73` | 14 | 4-4-2-3 | 17 | 2NT (Jacoby) | 4+ support, 13+ |
| `K843.73.QJ3.A842` | 10 | 4-2-3-4 | 11 | 3S (limit raise) | 3+ support, 10-12 |
| `QJ3.84.AKJ84.K97` | 14 | 3-2-5-3 | — | 2D (2-over-1) | 10+ HCP, 5+ diamonds |
| `Q84.73.J843.A973` | 6 | 3-2-4-4 | — | 1NT | 6-10, <3 support |

### Test Hands — Responses to 1D

| Hand | HCP | Shape | Support Pts | Expected | SAYC Rule |
|------|-----|-------|-------------|----------|-----------|
| `KJ84.A973.84.Q73` | 10 | 4-4-2-3 | — | 1H | 4-card major up the line |
| `K84.A973.QJ84.73` | 10 | 3-4-4-2 | — | 1H | 4-card major first |
| `K84.Q73.QJ84.973` | 8 | 3-3-4-3 | — | 2D (raise) | 4+ diamonds, 6-10, no major |
| `AQ3.K84.KJ84.973` | 13 | 3-3-4-3 | — | 2NT | 13-15 balanced, no major |
| `AKQ3.K84.KJ8.Q73` | 17 | 4-3-3-3 | — | 3NT | 16-17 balanced, no major |
| `843.973.J842.973` | 1 | 3-3-4-3 | — | Pass | <6 HCP |

### Test Hands — Responses to 1C

| Hand | HCP | Shape | Support Pts | Expected | SAYC Rule |
|------|-----|-------|-------------|----------|-----------|
| `KJ84.A973.Q73.84` | 10 | 4-4-3-2 | — | 1H | Major up the line |
| `K84.Q73.973.QJ84` | 8 | 3-3-3-4 | — | 1NT | 6-10, no major, <5 clubs |
| `K84.Q73.73.QJ984` | 8 | 3-3-2-5 | — | 2C (raise) | 5+ clubs, 6-10 |
| `843.973.973.J842` | 1 | 3-3-3-4 | — | Pass | <6 HCP |

### Integration Tests (in `test_sayc.py`)

Add hands that verify the full pipeline picks `response.*` rules when partner has opened:

```python
def test_limit_raise_over_1h():
    """Partner opens 1H, responder has 3+ support and 10-12 pts."""
    # Build auction: N opens 1H, E passes, S responds
    assert _response_select("K84.QJ3.A842.973", opening="1H") == "response.limit_raise_major"
```

## Implementation Order

1. `support_points` helper in `hand_eval.py` + tests
2. `response/major.py` — all major-specific + shared rules
3. `response/minor.py` — all minor-specific rules
4. `response/__init__.py` — re-exports
5. `sayc/__init__.py` — register all response rules
6. `tests/engine/rules/sayc/response/test_major.py`
7. `tests/engine/rules/sayc/response/test_minor.py`
8. `tests/engine/test_sayc.py` — add response integration tests
9. `pdm run check`

## Verification

```bash
pdm run test tests/evaluate/test_hand_eval.py
pdm run test tests/engine/rules/sayc/response/
pdm run test tests/engine/test_sayc.py
pdm run check
```

## Open Questions

1. ~~**Shared vs. separate rule classes**~~: **Resolved** — shared rules (jump shift, new suit 1-level, 2-over-1, pass) live in `major.py` and their `applies()` checks the opening bid type. Minor-only rules live in `minor.py`.

2. **Priority collisions with opening rules**: Response rules use `Category.RESPONSE`, opening rules use `Category.OPENING`. Since `RuleRegistry` enforces unique priorities *within* a category, there is no collision between opening priorities (50-450) and response priorities (50-380). The shared `response.pass` at priority 50 is in a different category than `opening.pass` at priority 50.

3. ~~**support_points vs distribution_points**~~: **Resolved** — `support_points = hcp + distribution_points(hand, trump_suit)`. The existing `distribution_points` function already handles trump suit exclusion. Minor raises do NOT use support points (use HCP only, per SAYC).

4. **Up-the-line suit selection**: When responding with a new suit at the 1-level and holding multiple 4-card suits, bid the cheapest (up the line) to avoid missing a fit. This is opposite to opening suit selection (bid the longest/highest). The `_find_cheapest_new_suit()` helper handles this.
