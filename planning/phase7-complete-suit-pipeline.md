# Phase 7: Complete All Bidding Pipelines

## Current State

117 rules registered, 675 tests passing.

- **Opening**: 9 rules (suit, NT, 2C, weak two, preempt 3/4) -- complete
- **Response to 1-of-a-suit**: 15 rules -- complete
- **Response to 1NT**: 11 rules -- complete (Phase B1)
- **Response to 2NT**: 8 rules -- complete (Phase B2)
- **Rebid after 1-of-a-suit**: 47 rules -- complete (Phase A)
- **Rebid after 1NT**: 17 rules -- complete (Phase B1)
- **Rebid after 2NT**: 10 rules -- complete (Phase B2)

---

## Phase A: Rebids After 1-of-a-Suit (COMPLETE)

17 rules added: pass after 3NT/4M, Jacoby 2NT (5), 2NT over minor (3), jump shift (4), help suit game try (1), double-jump bids (2).

All 1-of-a-suit response types now have matching rebid rules.

---

## Phase B1: Responses to 1NT + Rebids (COMPLETE)

11 response rules + 17 rebid rules. Stayman, Jacoby/Texas transfers, Gerber, 2NT/3NT/4NT, 3m invite, 2S puppet, pass. Opener rebids: Stayman replies, transfer completions, super-accept, Gerber response, accept/decline for 2NT/3m/3M/4NT.

See `planning/phase-b1-1nt-responses.md` for full detail.

---

## Phase B2: Responses to 2NT Opening (COMPLETE)

8 response rules + 10 rebid rules = 18 new rules. Mirrors 1NT but one level higher with adjusted HCP thresholds. No super-accept, no garbage Stayman, no 3m invite. Accept/decline 4NT at 20 vs 21 HCP.

### Context

2NT opening shows 20-21 HCP balanced. Responses mirror 1NT but one level higher, with adjusted ranges (partner needs less for game since 2NT is stronger).

References: `research/02-responses.md` (2NT responses), `research/05-conventions.md` (Stayman/transfers over 2NT).

### Response Rules (`response/nt.py` additions)

All use `Category.RESPONSE`. Each rule's `applies()` checks `_opened_2nt(ctx)`.

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `RespondGerberOver2NT` | 4C | 13+ HCP, balanced, no 5+ major (slam interest) | 494 |
| 2 | `Respond4NTOver2NT` | 4NT | 11-12 HCP, balanced (quantitative invite to 6NT) | 484 |
| 3 | `RespondTexasOver2NT` | 4D/4H | 6+ card major, game values, no slam interest | 464 |
| 4 | `RespondStaymanOver2NT` | 3C | 5+ HCP, 4+ major, not 4-3-3-3 | 444 |
| 5 | `RespondTransferOver2NT` | 3D/3H | 5+ card major (transfer) | 434 |
| 6 | `Respond3NTOver2NT` | 3NT | 4-10 HCP, no 4+ major or 4-3-3-3 | 424 |
| 7 | `Respond3SPuppetOver2NT` | 3S | Weak, 6+ card minor (puppet to 4C) | 394 |
| 8 | `RespondPassOver2NT` | Pass | 0-3 HCP, no shape | 44 |

**Key differences from 1NT responses:**
- No 2NT invite (already at 2NT)
- No 3m invite (3C is Stayman, 3D/3H are transfers)
- Puppet is 3S (not 2S), relays to 4C (not 3C)
- Lower HCP thresholds for game (opener has 20-21)
- No garbage Stayman (responder can pass 2NT with weak hands)

### Rebid Rules (`rebid/nt.py` additions)

All use `Category.REBID_OPENER`. Each rule's `applies()` checks `_opened_2nt_self(ctx)`.

#### After Stayman (3C)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTStayman3H` | 3H | 4+ hearts (hearts first with both) | 574 |
| `Rebid2NTStayman3S` | 3S | 4+ spades, <4 hearts | 569 |
| `Rebid2NTStayman3D` | 3D | No 4-card major | 564 |

#### After Jacoby Transfer (3D/3H)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTCompleteTransfer` | 3H/3S | Complete transfer at cheapest level | 554 |

Note: No super-accept over 2NT -- already at max range, just complete.

#### After 3S Puppet

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTComplete3SPuppet` | 4C | Forced relay | 551 |

#### After Gerber (4C)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTGerberResponse` | 4D/4H/4S/4NT | By ace count (same step responses) | 549 |

#### After Texas (4D/4H)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTCompleteTexas` | 4H/4S | Complete Texas transfer | 544 |

#### After 3NT

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTPassAfter3NT` | Pass | Always | 509 |

#### After 4NT (quantitative)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTAccept4NT` | 6NT | 21 HCP (max) | 504 |
| `Rebid2NTDecline4NT` | Pass | 20 HCP (min) | 499 |

### Files

| File | Change |
|------|--------|
| `src/bridge/engine/rules/sayc/response/nt.py` | Add 8 response rules + `_opened_2nt()` helper |
| `src/bridge/engine/rules/sayc/rebid/nt.py` | Add 10 rebid rules + `_opened_2nt_self()` helper |
| `src/bridge/engine/rules/sayc/response/__init__.py` | Add exports |
| `src/bridge/engine/rules/sayc/rebid/__init__.py` | Add exports |
| `src/bridge/engine/rules/sayc/__init__.py` | Register all ~18 new rules |
| `tests/engine/rules/sayc/response/test_nt.py` | Add 2NT response tests |
| `tests/engine/rules/sayc/rebid/test_nt.py` | Add 2NT rebid tests |
| `tests/engine/test_sayc.py` | Integration tests |

### Priority conflict analysis

| Hand | Applicable rules | Winner | Correct? |
|------|-----------------|--------|----------|
| 5H, 8 HCP | Transfer (434), 3NT (424) | Transfer | Yes |
| 6H, 8 HCP | Texas (464), Transfer (434) | Texas | Yes -- game signoff |
| 4H, 5 HCP | Stayman (444), 3NT (424) | Stayman | Yes |
| 4-3-3-3, 8 HCP | 3NT (424) | 3NT | Yes -- flat |
| 0 HCP flat | Pass (44) | Pass | Yes |

---

## Phase B3: Responses to 2C Opening (~4 response + ~6 rebid rules)

### Context

2C is strong, artificial, forcing. Partner MUST respond. After 2C-2D (waiting), opener rebids naturally: 2NT (22-24), 3NT (25-27), or a suit. After 2C-2D-2NT, responder uses the 2NT response structure (Stayman, transfers -- shared with B2).

References: `research/02-responses.md` (2C responses), `research/01-opening-bids.md` (2C rebids).

### Response Rules (`response/strong.py` -- new file)

All use `Category.RESPONSE`. Each checks `_opened_2c(ctx)`.

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `Respond2NTOver2C` | 2NT | 8+ HCP, balanced (positive) | 490 |
| 2 | `RespondPositiveSuitOver2C` | 2H/2S/3C/3D | 8+ HCP, 5+ card suit, 2+ of top 3 honors | 480 |
| 3 | `Respond2DWaiting` | 2D | Default (any hand -- artificial waiting) | 470 |

Note: `Respond2DWaiting` is the catch-all. Positive responses (2NT, suit) take priority when their conditions are met. 2D is artificial and says nothing about diamonds.

### Rebid Rules (`rebid/strong.py` -- new file)

Opener's rebid after 2C opening. All use `Category.REBID_OPENER`.

#### After 2D (waiting)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `Rebid2NTAfter2C` | 2NT | 22-24 HCP, balanced | 590 |
| `Rebid3NTAfter2C` | 3NT | 25-27 HCP, balanced | 585 |
| `RebidSuitAfter2C` | 2H/2S/3C/3D | 5+ card suit, natural, forcing | 580 |

Note: After 2C-2D-2NT, responder uses the 2NT response structure (B2 rules handle this -- Stayman at 3C, transfers at 3D/3H, etc.).

#### After positive suit response

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidRaisePositive` | Raise partner's suit | 4+ support | 578 |
| `RebidSuitAfterPositive` | Own suit | 5+ cards, natural | 576 |
| `RebidNTAfterPositive` | 3NT | Balanced, no fit | 574 |

### Forcing rules

- After positive response: game forcing (neither player may pass below game)
- After 2D-suit: forcing to 3M or 4m
- After 2D-2NT: NOT forcing (responder may pass with very weak hand)

### Files

| File | Change |
|------|--------|
| `src/bridge/engine/rules/sayc/response/strong.py` | New: 3 response rules |
| `src/bridge/engine/rules/sayc/rebid/strong.py` | New: 6 rebid rules |
| `src/bridge/engine/rules/sayc/response/__init__.py` | Add exports |
| `src/bridge/engine/rules/sayc/rebid/__init__.py` | Add exports |
| `src/bridge/engine/rules/sayc/__init__.py` | Register ~9 new rules |
| Tests | Unit + integration tests |

---

## Phase B4: Responses to Weak Twos (~6 response + ~6 rebid rules)

### Context

Weak two openings (2D/2H/2S) show 5-11 HCP, 6-card suit. Responses focus on: raise (preemptive or game), 2NT feature ask, new suit (forcing one round), 3NT to play.

References: `research/02-responses.md` (weak two responses), `research/02-responses.md` (opener rebids after 2NT ask and new suit).

### Response Rules (`response/preempt.py` -- new file)

All use `Category.RESPONSE`. Each checks `_opened_weak_two(ctx)`.

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `RespondGameRaiseWeakTwo` | 4H/4S/5D | Game raise (to play, may be preemptive) | 488 |
| 2 | `Respond3NTOverWeakTwo` | 3NT | Stopper in all side suits, game values | 486 |
| 3 | `RespondNewSuitOverWeakTwo` | New suit | 5+ cards, forcing one round (RONF) | 482 |
| 4 | `Respond2NTFeatureAsk` | 2NT | Game interest, forcing (asks for feature) | 478 |
| 5 | `RespondRaiseWeakTwo` | 3D/3H/3S | Preemptive raise, fit, weak | 476 |
| 6 | `RespondPassOverWeakTwo` | Pass | Default | 46 |

### Rebid Rules (`rebid/preempt.py` -- new file)

#### After 2NT feature ask

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidShowFeature` | New suit at 3-level | Maximum (9-11 HCP), outside ace or protected king | 588 |
| `Rebid3NTAfterFeatureAsk` | 3NT | Maximum, no outside feature to show | 586 |
| `RebidOwnSuitAfterFeatureAsk` | Rebid own suit at 3-level | Minimum (5-8 HCP) | 584 |

#### After new suit response

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidRaiseNewSuitOverWeakTwo` | Raise partner's suit | 3+ card support | 582 |
| `RebidOwnSuitOverNewSuit` | Rebid own suit | No fit, minimum | 579 |

#### After raise / 3NT / game raise

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidPassAfterWeakTwoRaise` | Pass | Always (raise is to play) | 577 |

### Files

| File | Change |
|------|--------|
| `src/bridge/engine/rules/sayc/response/preempt.py` | New: 6 response rules |
| `src/bridge/engine/rules/sayc/rebid/preempt.py` | New: 6 rebid rules |
| Registration + tests as usual |

---

## Phase B5: Responses to 3-Level Preempts (~5 response + ~3 rebid rules)

### Context

3-level preempts (3C/3D/3H/3S) show ~5-10 HCP, 7-card suit. Limited responses.

References: `research/02-responses.md` (3-level preempt responses).

### Response Rules (add to `response/preempt.py`)

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `RespondGameRaise3Level` | 4M/5m | Game raise (to play) | 487 |
| 2 | `Respond3NTOver3Level` | 3NT | Stoppers, game values | 485 |
| 3 | `RespondNewSuitOver3Level` | New suit below game | 5+ cards, forcing one round | 481 |
| 4 | `RespondRaise3Level` | Raise (4-level) | Preemptive, fit | 475 |
| 5 | `RespondPassOver3Level` | Pass | Default | 43 |

### Rebid Rules (add to `rebid/preempt.py`)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidRaiseAfterNewSuit3Level` | Raise partner's suit | 3+ support | 575 |
| `RebidOwnSuitAfterNewSuit3Level` | Rebid own suit | No fit | 573 |
| `RebidPassAfter3LevelResponse` | Pass | After 3NT / game raise / raise | 571 |

### Files

Add to `response/preempt.py` and `rebid/preempt.py`.

---

## Phase B6: Responses to 4-Level Preempts (~2 response + ~1 rebid rules)

### Context

4-level preempts (4C/4D/4H/4S) show ~8+ card suit. Very limited responses -- mostly pass.

### Response Rules (add to `response/preempt.py`)

| # | Rule | Bid | Condition | Priority |
|---|------|-----|-----------|----------|
| 1 | `RespondRaise4Level` | 5m/game raise | Strong hand, fit | 474 |
| 2 | `RespondPassOver4Level` | Pass | Default | 42 |

### Rebid Rules (add to `rebid/preempt.py`)

| Rule | Bid | Condition | Priority |
|------|-----|-----------|----------|
| `RebidPassAfter4Level` | Pass | Always | 570 |

---

## Phase B Summary

| Phase | Opening type | New response rules | New rebid rules | Total new | Status |
|-------|-------------|-------------------|-----------------|-----------|--------|
| B1 | 1NT (15-17) | 11 | 17 | 28 | COMPLETE |
| B2 | 2NT (20-21) | 8 | 10 | 18 | COMPLETE |
| B3 | 2C (strong) | 3 | 6 | 9 | Planned |
| B4 | Weak twos | 6 | 6 | 12 | Planned |
| B5 | 3-level preempts | 5 | 3 | 8 | Planned |
| B6 | 4-level preempts | 2 | 1 | 3 | Planned |
| **Total** | | **35** | **43** | **78** | |

After Phase B: 99 + 78 = ~177 rules, covering every opening bid type through opener's rebid.

## Implementation Order

B2 first (2NT shares the most machinery with B1), then B3 (2C), then B4-B6 (preempts).

## What Remains After Phase B

| Gap | Phase | Scope |
|-----|-------|-------|
| Responder's second bid (reresponse) | C | After Stayman, after transfers complete, after game tries, etc. |
| Further bidding (rounds 5+) | D | Later auction continuations |
| Competitive bidding | E | Overcalls, takeout doubles, advances -- cuts across all rounds |

---

## Verification

After each sub-phase:
```bash
pdm run check   # lint + typecheck + all tests
```
