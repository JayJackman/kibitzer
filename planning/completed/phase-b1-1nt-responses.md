# Phase B1: Responses to 1NT Opening + Opener Rebids

## Context

Phase 7A completed all rebid rules for 1-of-a-suit openings (47 rebid rules, 65 total). The next gap is responses to 1NT openings --- currently the engine falls through to `fallback.pass` for any hand responding to 1NT. This phase adds response rules (what responder bids after partner opens 1NT) and rebid rules (how opener rebids after responder acts).

References: `research/02-responses.md` (1NT responses), `research/05-conventions.md` (Stayman, Jacoby Transfers, Gerber), `research/06-slam.md` (Gerber responses, quantitative 4NT).

## Response Rules (`response/nt.py`) --- 12 rules

All use `Category.RESPONSE`. Each rule's `applies()` first checks `_opened_1nt(ctx)`.

### Helpers

```python
def _opened_1nt(ctx: BiddingContext) -> bool:
    """Partner opened 1NT."""

def _has_4_card_major(ctx: BiddingContext) -> bool:
    """Responder has at least one 4-card major."""

def _has_5_card_major(ctx: BiddingContext) -> bool:
    """Responder has a 5+ card major."""

def _is_4333(ctx: BiddingContext) -> bool:
    """Responder has 4-3-3-3 shape (flat)."""
```

### Rules (descending priority)

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `RespondGerber` | 4C | 18+ HCP, balanced, no 5+ major | 495 |
| 2 | `Respond4NTOver1NT` | 4NT | 15-17 HCP, balanced | 485 |
| 3 | `Respond3MajorOver1NT` | 3H/3S | 6+ card major, 16+ HCP (slam interest) | 475 |
| 4 | `RespondTexasTransfer` | 4D/4H | 6+ card major, 10-15 HCP (game, no slam) | 465 |
| 5 | `RespondStayman` | 2C | (8+ HCP, 4+ major, no 5+ major, not 4-3-3-3) OR (4-4+ majors, any HCP = garbage Stayman) | 445 |
| 6 | `RespondJacobyTransfer` | 2D/2H | 5+ card major (transfer to that major) | 435 |
| 7 | `Respond3NTOver1NT` | 3NT | 10-15 HCP, no 4+ major or 4-3-3-3 shape | 425 |
| 8 | `Respond3MinorOver1NT` | 3C/3D | 6+ card minor, 8-9 HCP (invite) | 415 |
| 9 | `Respond2NTOver1NT` | 2NT | 8-9 HCP, balanced, no 4+ major (or 4-3-3-3) | 405 |
| 10 | `Respond2SPuppet` | 2S | Weak hand (0-7), 6+ card minor (sign-off mechanism) | 395 |
| 11 | `RespondPassOver1NT` | Pass | 0-7 HCP, no 5+ major, no 6+ minor, no 4-4 majors | 45 |

**Note**: `RespondJacobyTransfer` is one rule class that handles both 2D (hearts) and 2H (spades). With both 5+ majors, transfer to the longer; equal length, transfer to spades.

### Priority conflict analysis

| Hand | Applicable rules | Winner | Correct? |
|------|-----------------|--------|----------|
| 5H, 10 HCP | Transfer (435), 3NT (425) | Transfer | Yes --- transfer then bid 3NT |
| 6H, 10 HCP | Texas (465), Transfer (435) | Texas | Yes --- game signoff |
| 6H, 16 HCP | 3M slam (475), Texas (465) | 3M slam | Yes --- slam interest |
| 4H, 10 HCP | Stayman (445), 3NT (425) | Stayman | Yes --- look for fit |
| 4H 4-3-3-3, 10 HCP | 3NT (425) | 3NT | Yes --- too flat for Stayman |
| 4-4 majors, 3 HCP | Stayman (445), Pass (45) | Stayman | Yes --- garbage Stayman |
| 6C, 5 HCP | 2S puppet (395), Pass (45) | 2S puppet | Yes --- sign off in 3C |
| 5H, 0 HCP | Transfer (435), Pass (45) | Transfer | Yes --- sign off in 2H |

## Rebid Rules (`rebid/nt.py`) --- 17 rules

All use `Category.REBID_OPENER`. Each rule's `applies()` first checks `_opened_1nt_self(ctx)`.

### Helpers

```python
def _opened_1nt_self(ctx: BiddingContext) -> bool:
    """I opened 1NT (my first bid was 1NT)."""

def _partner_response(ctx: BiddingContext) -> SuitBid:
    """Partner's response bid (always a SuitBid after 1NT opening)."""

def _partner_bid_stayman(ctx: BiddingContext) -> bool:
    """Partner bid 2C (Stayman)."""

def _partner_transferred(ctx: BiddingContext) -> bool:
    """Partner bid 2D (hearts) or 2H (spades) --- Jacoby transfer."""

def _transfer_suit(ctx: BiddingContext) -> Suit:
    """The suit partner transferred to (hearts if 2D, spades if 2H)."""

def _partner_bid_texas(ctx: BiddingContext) -> bool:
    """Partner bid 4D or 4H --- Texas transfer."""

def _texas_suit(ctx: BiddingContext) -> Suit:
    """The suit partner Texas-transferred to."""

def _ace_count(ctx: BiddingContext) -> int:
    """Count aces in opener's hand (for Gerber response)."""
```

### Rules (grouped by response type)

#### After Stayman (2C)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidStayman2H` | 2H | 4+ hearts (bid hearts first with both majors) | 575 |
| `RebidStayman2S` | 2S | 4+ spades, <4 hearts | 570 |
| `RebidStayman2D` | 2D | No 4-card major | 565 |

#### After Jacoby Transfer (2D/2H)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidSuperAccept` | 3H/3S | 17 HCP, 4+ card support for transfer suit | 560 |
| `RebidCompleteTransfer` | 2H/2S | Complete transfer at cheapest level (default) | 555 |

#### After 2S Puppet

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidComplete2SPuppet` | 3C | Always (forced response to 2S puppet) | 552 |

#### After Gerber (4C)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidGerberResponse` | 4D/4H/4S/4NT | By ace count: 0/4=4D, 1=4H, 2=4S, 3=4NT | 550 |

#### After Texas Transfer (4D/4H)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidCompleteTexas` | 4H/4S | Complete Texas transfer | 545 |

#### After 3H/3S (slam interest)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidRaise3MajorOver1NT` | 4H/4S | 3+ support, 16-17 HCP (max) | 540 |
| `RebidDecline3MajorOver1NT` | 3NT | <3 support or 15 HCP (min) | 535 |

#### After 2NT (invite)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidAccept2NTOver1NT` | 3NT | 16-17 HCP (max) | 530 |
| `RebidDecline2NTOver1NT` | Pass | 15 HCP (min) | 525 |

#### After 3C/3D (minor invite)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidAccept3MinorOver1NT` | 3NT | 16-17 HCP (max) | 520 |
| `RebidDecline3MinorOver1NT` | Pass | 15 HCP (min) | 515 |

#### After 3NT

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidPassAfter3NTOver1NT` | Pass | Always | 510 |

#### After 4NT (quantitative)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidAccept4NTOver1NT` | 6NT | 16-17 HCP (max) | 505 |
| `RebidDecline4NTOver1NT` | Pass | 15 HCP (min) | 500 |

## Files to Create

| File | Content |
|------|---------|
| `src/bridge/engine/rules/sayc/response/nt.py` | 12 response rule classes + helpers |
| `src/bridge/engine/rules/sayc/rebid/nt.py` | 17 rebid rule classes + helpers |
| `tests/engine/rules/sayc/response/test_nt.py` | Unit tests for each response rule |
| `tests/engine/rules/sayc/rebid/test_nt.py` | Unit tests for each rebid rule |

## Files to Modify

| File | Change |
|------|--------|
| `src/bridge/engine/rules/sayc/response/__init__.py` | Add imports + `__all__` entries for new classes |
| `src/bridge/engine/rules/sayc/rebid/__init__.py` | Add imports + `__all__` entries for new classes |
| `src/bridge/engine/rules/sayc/__init__.py` | Import + register all 29 new rules with section comments |
| `tests/engine/test_sayc.py` | Add `_1nt_response_select()` and `_1nt_rebid_select()` integration helpers + smoke tests |

## Implementation Order

1. Response helpers + rules (`response/nt.py`) --- all 12 rules
2. Response exports (`response/__init__.py`)
3. Response tests (`tests/.../response/test_nt.py`)
4. Rebid helpers + rules (`rebid/nt.py`) --- all 17 rules
5. Rebid exports (`rebid/__init__.py`)
6. Rebid tests (`tests/.../rebid/test_nt.py`)
7. Registration (`sayc/__init__.py`) --- wire up all 29 rules
8. Integration tests (`tests/engine/test_sayc.py`)
9. `pdm run check` --- fix any issues

## Key Design Decisions

1. **No 4-3-3-3 Stayman**: Per research/05-conventions.md, 4-3-3-3 flat hands should bid NT directly, not Stayman. Even with a 4-card major.

2. **Transfer > Stayman for 5+ major**: With 5+ card major, always transfer. Stayman only applies with exactly 4-card major (no 5+ major). Exception: garbage Stayman (4-4+ majors, 0-7 HCP).

3. **Super-accept IS SAYC**: Jump to 3M with 17 HCP and 4+ trumps (research/05-conventions.md line 96).

4. **Gerber response mapping**: 4D=0/4 aces, 4H=1, 4S=2, 4NT=3 (research/06-slam.md).

5. **No selector/phase changes needed**: `detect_phase()` already returns `RESPONSE` for responder's first bid and `REBID_OPENER` for opener's rebid, regardless of opening bid type.

6. **NT bids are SuitBid**: `SuitBid(1, Suit.NOTRUMP)` --- consistent with existing design.

## Priority Map (All Response Rules After B1)

```
Responses to 1-of-a-suit (existing):
380  RespondJumpShift
360  RespondJacoby2NT
340  RespondGameRaiseMajor
320  Respond3NTOverMajor
310  Respond3NTOverMinor
300  Respond2NTOverMinor
280  RespondLimitRaiseMajor
270  RespondLimitRaiseMinor
260  RespondNewSuit1Level
240  Respond2Over1
230  RespondSingleRaiseMinor
220  RespondSingleRaiseMajor
210  Respond1NTOverMinor
200  Respond1NTOverMajor
 50  RespondPass

Responses to 1NT (new):
495  RespondGerber
485  Respond4NTOver1NT
475  Respond3MajorOver1NT
465  RespondTexasTransfer
445  RespondStayman
435  RespondJacobyTransfer
425  Respond3NTOver1NT
415  Respond3MinorOver1NT
405  Respond2NTOver1NT
395  Respond2SPuppet
 45  RespondPassOver1NT
```

## Verification

```bash
pdm run check   # lint + typecheck + all tests must pass
```

Key checks:
- All existing 487 tests still pass
- New response tests cover each rule with representative hands
- New rebid tests cover each Stayman/Transfer/Gerber/etc. response
- Integration tests verify full pipeline: hand -> response -> rebid
- No priority conflicts in RuleRegistry (unique per category)
