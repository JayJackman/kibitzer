# Phase 7: Complete the 1-of-a-suit Pipeline

## Context

Phases 1–6 built the foundation: domain model, hand evaluation, rule engine, opening bids, responses to 1-of-a-suit, and opener's rebids after 5 response types. The system has 54 rules (9 opening + 15 response + 30 rebid).

However, opener's rebid only handles 5 of the 11 possible response types after a 1-of-a-suit opening. The remaining 6 response types (Jacoby 2NT, jump shift, 3NT, 4M preemptive raise, 2NT over minor) have no rebid rules — the engine falls through to `fallback.pass` with an unhelpful "No applicable rule" message.

This phase fills every gap so that **every uncontested auction starting with 1-of-a-suit produces a bid from a matching rule**.

## Audit Results

### Openings: Complete
Open3NT (25-27 HCP balanced) is listed in SAYC as valid, but these hands already open 2C (priority 450) and rebid 3NT. Both paths reach the same contract. **Decision: skip** — 2C path is the standard approach.

### Responses to 1-of-a-suit: Complete
All 17 response types (+ pass) are implemented. No gaps.

### Rebids after 1-of-a-suit: 6 gaps

| Response type | Current rules | Gap |
|---|---|---|
| Single raise (2M/2m) | 6 rules | Missing: help suit game tries |
| Limit raise (3M/3m) | 5 rules | Complete |
| 1NT response | 7 rules | Complete |
| New suit 1-level | 9 rules | Missing: double-jump raise + double-jump rebid own suit |
| 2-over-1 | 5 rules | Complete |
| **Jacoby 2NT** | **0 rules** | **5 new rules needed** |
| **Jump shift** | **0 rules** | **4 new rules needed** |
| **3NT response** | **0 rules** | **1 pass rule needed** |
| **4M preemptive raise** | **0 rules** | **1 pass rule needed** |
| **2NT over minor** | **0 rules** | **3 new rules needed** |
| Pass | N/A | No rebid needed |

**Total: 17 new rules needed**

---

## Phase A: Deliverables

All changes go in existing files. No new files needed.

### A1: Pass rules for game-level responses (2 rules)

Simplest gap — explicit pass rules so the engine gives proper explanations instead of falling through to the generic fallback.

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidPassAfter3NT` | Pass | Partner bid 3NT (over major or minor) | 55 |
| `RebidPassAfterGameRaise` | Pass | Partner bid 4M (preemptive raise) | 56 |

New classifiers: `_partner_bid_3nt()`, `_partner_bid_game_raise()`

### A2: Rebids after Jacoby 2NT (5 rules)

Reference: `research/03-rebids.md` "After Jacoby 2NT"

Game-forcing raise with 4+ trumps and 13+ dummy points. Trump suit is established. Opener describes hand shape and strength:

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidJacoby3LevelShortness` | 3x new suit | Singleton/void in that suit | 440 |
| `RebidJacoby4LevelSource` | 4x new suit | 5+ card side suit (source of tricks) | 430 |
| `RebidJacoby3Major` | 3M (agreed) | 18+ total pts, no shortness, no 5-card side suit | 420 |
| `RebidJacoby3NT` | 3NT | 15-17 total pts, no shortness, no 5-card side suit | 410 |
| `RebidJacoby4Major` | 4M (agreed) | 12-14 total pts, no shortness (minimum, sign-off) | 400 |

New classifier: `_partner_bid_jacoby_2nt()` — partner responded 2NT to our 1M opening

New helpers:
- `_find_shortness_suit(ctx)` — find a side suit with 0 or 1 cards
- `_find_5_card_side_suit(ctx)` — find a side suit with 5+ cards

Priority ordering: shortness (most descriptive) > source of tricks > strength tiers. When opener has shortness, always show it. When opener has a side source, show it. Otherwise, bid based on strength.

### A3: Rebids after 2NT over minor (3 rules)

After 1m→2NT (13-15 HCP balanced, game forcing). Opener describes hand naturally:

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidShowMajorAfter2NTMinor` | 3H or 3S | Has 4-card major (bid hearts first with both) | 395 |
| `RebidMinorAfter2NTMinor` | 3m (own minor) | 6+ cards in minor, no 4-card major | 392 |
| `RebidNTAfter2NTMinor` | 3NT | Balanced catch-all (no 4-card major, <6 in minor) | 390 |

New classifier: `_partner_bid_2nt_over_minor()` — partner responded 2NT to our 1m opening

### A4: Rebids after jump shift (4 rules)

Reference: `research/03-rebids.md` "After a Jump Shift"

Game forcing (19+ HCP from responder, slam interest). Opener cannot pass — must describe hand:

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidRaiseAfterJumpShift` | Raise responder's suit | 4+ card support | 460 |
| `RebidOwnSuitAfterJumpShift` | Rebid own suit | 6+ cards | 455 |
| `RebidNewSuitAfterJumpShift` | New (third) suit | 4+ cards, natural | 450 |
| `RebidNTAfterJumpShift` | NT | Balanced catch-all | 445 |

New classifier: `_partner_jump_shifted()` — response is a new suit one level higher than the cheapest possible. This is the trickiest classifier because it must compute what the "cheapest" bid in responder's suit would have been.

Jump shift detection logic:
- Response is a suit bid (not NT, not pass)
- Response suit differs from opening suit
- Response level > cheapest legal level for that suit

For example, after 1H: 1S is NOT a jump shift (cheapest level), but 2S IS. After 1D: 1H is NOT a jump shift, but 2H IS. After 1C: 2D IS a jump shift (could have bid 1D).

### A5: Help suit game tries (1 rule)

Reference: `research/03-rebids.md` "After a Single Raise" — "New suit: Natural, game try"

After 1M→2M, opener bids a new suit at the 3-level to ask responder about help in that suit. Applies in the invitational range where a simple 3M is also an option:

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidHelpSuitGameTry` | 3x new suit | 16-18 Bergen pts, major raise only, has a 3+ card side suit | 215 |

Priority 215: between `RebidInviteAfterRaiseMajor` (220) and `Rebid2NTAfterRaiseMinor` (210). When opener has a specific suit needing help, the game try is more informative than a generic 3M invite.

The bid suit should be one where opener has losers and wants help (e.g., Qxx, xxx). Simple heuristic: bid the longest side suit; with ties, bid the cheapest.

Note: Responder's handling of game tries goes in `reresponse/` in a future phase.

### A6: Double-jump bids after new suit 1-level (2 rules)

Reference: `research/03-rebids.md` "Maximum (19-21 points)" section

| Rule | Bid | Condition | Priority |
|---|---|---|---|
| `RebidDoubleJumpRaiseResponder` | 4x responder's suit | 19+ total pts, 4+ card support | 385 |
| `RebidDoubleJumpRebidOwnSuit` | 4x own suit | 19+ total pts, 6+ card self-supporting suit | 383 |

These differ from existing jump bids (`RebidJumpRaiseResponder` at 280 for 17-18 pts, `RebidJumpRebidOwnSuit` at 240 for 17-18 pts) by going directly to game level.

---

## Files to Modify

| File | Change |
|---|---|
| `src/bridge/engine/rules/sayc/rebid/suit.py` | Add 17 new rule classes + classifiers + helpers |
| `src/bridge/engine/rules/sayc/rebid/__init__.py` | Add exports for all 17 new classes |
| `src/bridge/engine/rules/sayc/__init__.py` | Register 17 new rules in `create_sayc_registry()` |
| `tests/engine/rules/sayc/rebid/test_suit.py` | Add test classes for each group |
| `tests/engine/test_sayc.py` | Add integration tests for new rebid scenarios |

## Implementation Order

1. A1 (pass rules) — simplest, eliminates fallback errors
2. A2 (Jacoby 2NT) — 5 rules, self-contained
3. A3 (2NT over minor) — 3 rules, straightforward
4. A4 (jump shift) — 4 rules, needs jump-shift classifier
5. A5 (help suit game try) — 1 rule
6. A6 (double-jump bids) — 2 rules
7. `pdm run check`

**Total: 17 new rules → 47 rebid rules, 65 total rules in registry**

## Completeness Check After Phase A

Every response to 1-of-a-suit will have a matching rebid rule:

| Response | Rebid coverage |
|---|---|
| Pass by responder | N/A (no rebid needed) |
| Single raise | Pass / invite / game / help suit game try |
| Limit raise | Accept / decline |
| 1NT | 7 options (pass through 3NT) |
| New suit 1-level | 11 options (including double-jumps) |
| 2-over-1 | 5 options |
| Jacoby 2NT | 5 options (shortness / source / strength tiers) |
| Jump shift | 4 options (raise / rebid / new suit / NT) |
| 3NT | Pass |
| 4M preemptive | Pass |
| 2NT over minor | 3 options (show major / rebid minor / 3NT) |

## Priority Map (All Rebid Rules After Phase 7)

```
460  RebidRaiseAfterJumpShift         (A4)
455  RebidOwnSuitAfterJumpShift       (A4)
450  RebidNewSuitAfterJumpShift       (A4)
445  RebidNTAfterJumpShift            (A4)
440  RebidJacoby3LevelShortness       (A2)
430  RebidJacoby4LevelSource          (A2)
420  RebidJacoby3Major                (A2)
410  RebidJacoby3NT                   (A2)
400  RebidJacoby4Major                (A2)
395  RebidShowMajorAfter2NTMinor      (A3)
392  RebidMinorAfter2NTMinor          (A3)
390  RebidNTAfter2NTMinor             (A3)
385  RebidDoubleJumpRaiseResponder    (A6)
383  RebidDoubleJumpRebidOwnSuit      (A6)
380  RebidJumpTo2NT                   (existing)
370  RebidJumpShiftNewSuit            (existing)
360  Rebid3NTOver1NT                  (existing)
340  RebidJumpShiftOver1NT            (existing)
320  Rebid3NTAfterRaiseMinor          (existing)
310  RebidAcceptLimitRaiseMajor       (existing)
300  RebidGameAfterRaiseMajor         (existing)
290  RebidRaise2Over1Responder        (existing)
280  RebidJumpRaiseResponder          (existing)
270  RebidNewSuitAfter2Over1          (existing)
260  RebidReverse                     (existing)
250  Rebid2NTOver1NT                  (existing)
240  RebidJumpRebidOwnSuit            (existing)
230  RebidJumpRebidOver1NT            (existing)
220  RebidInviteAfterRaiseMajor       (existing)
215  RebidHelpSuitGameTry             (A5)
210  Rebid2NTAfterRaiseMinor          (existing)
200  RebidNTAfter2Over1Max            (existing)
190  RebidSuitAfter2Over1             (existing)
180  Rebid5mAfterLimitRaiseMinor      (existing)
170  RebidNewSuitAfterRaiseMinor      (existing)
160  RebidRaiseResponder              (existing)
150  RebidNewLowerSuitOver1NT         (existing)
140  RebidNewSuitNonreverse           (existing)
130  RebidSuitOver1NT                 (existing)
120  RebidOwnSuit                     (existing)
110  RebidNTAfter2Over1Min            (existing)
100  Rebid1NT                         (existing)
 70  RebidDeclineLimitRaise           (existing)
 60  RebidPassAfterRaise              (existing)
 56  RebidPassAfterGameRaise          (A1)
 55  RebidPassAfter3NT                (A1)
 50  RebidPassOver1NT                 (existing)
```

---

## Phase B: Complete All Responses + All Rebids (Later)

Organized by opening bid type. Each sub-phase creates new response + rebid files.

### B1: Responses to 1NT opening (~12 response + ~12 rebid rules)

**Files**: `response/nt.py`, `rebid/nt.py`

Responses: Pass, Stayman (2C), Jacoby transfers (2D→hearts, 2H→spades), minor puppet (2S), 2NT invite, 3C/3D invite, 3H/3S slam interest, 3NT, Gerber (4C), Texas transfers (4D/4H), quantitative 4NT

Rebids: Complete Stayman (2D/2H/2S), complete transfers (accept/super-accept), complete puppet (3C forced), accept/decline 2NT, respond to Gerber, accept/decline 4NT

### B2: Responses to 2NT opening (~7 response + ~8 rebid rules)

**Files**: Add to `response/nt.py`, `rebid/nt.py`

Similar to 1NT but one level higher: Stayman (3C), transfers (3D/3H), puppet (3S), 3NT, Gerber (4C), quantitative 4NT

### B3: Responses to 2C opening (~4 response + ~8 rebid rules)

**Files**: `response/strong.py`, `rebid/strong.py`

Responses: 2D waiting, positive suit bids (5+ cards, 8+ HCP), 2NT balanced positive

Rebids: 2NT (22-24 balanced), 3NT (25-27 balanced), suit bids (natural), jump in suit (self-supporting)

Note: After 2C→2D→2NT, responder uses 2NT response structure (can share with B2).

### B4: Responses to weak twos (~5 response + ~6 rebid rules)

**Files**: `response/preempt.py`, `rebid/preempt.py`

Responses: Raise (preemptive), 2NT feature ask, 3NT, new suit (forcing, RONF), game raise

Rebids after 2NT ask: Rebid own suit (min), show feature (max), 3NT (max no feature)
Rebids after new suit: Raise (3+ support), rebid own suit (no fit)

### B5: Responses to 3-level preempts (~4 response + ~4 rebid rules)

**Files**: Add to `response/preempt.py`, `rebid/preempt.py`

Responses: Raise, 3NT, new suit (forcing), game raise
Rebids: Mostly pass; after new suit, raise with support or rebid

### B6: Responses to 3NT/4-level openings (~3 response + ~2 rebid rules)

**Files**: Add to existing files

Minimal — mostly pass or raise. Rare in practice.

### Phase B estimated totals

~35 new response rules + ~40 new rebid rules = ~75 new rules

### No Category/selector changes needed

`Category.REBID_OPENER` and `Category.RESPONSE` cover all Phase A and B scenarios. The `detect_phase()` logic already handles these correctly. Future `RERESPONSE` and `FURTHER` categories are only needed when implementing rounds 4+.

---

## Verification

After each deliverable:
```bash
pdm run check   # lint + type check + all tests
```
