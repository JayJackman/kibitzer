# Phase 4: Opening Bid Rules

## Context

Phases 1–3 are complete: domain model, hand evaluation, and the rule engine skeleton. Phase 4 implements the first real SAYC rules — opening bids. This is the simplest category because there is no prior auction context (no partner bids, no opponent interference). It validates the full architecture end-to-end with real bidding logic.

All rules in this phase must be accurate to the ACBL SAYC System Booklet (SP-3, revised January 2006). The reference material lives in `research/01-opening-bids.md` and `research/00-overview.md`.

## Files

| File | Action |
|------|--------|
| `src/bridge/evaluate/hand_eval.py` | Update — add suit_quality, best_major, best_minor, rule_of_20, rule_of_15, has_outside_four_card_major |
| `src/bridge/evaluate/__init__.py` | Update — re-export new functions |
| `src/bridge/engine/rules/opening.py` | Create — 1-level suit opening rules |
| `src/bridge/engine/rules/opening_nt.py` | Create — 1NT, 2NT opening rules |
| `src/bridge/engine/rules/opening_strong.py` | Create — 2C strong artificial opening |
| `src/bridge/engine/rules/opening_preempt.py` | Create — Weak twos, 3-level preempts, 4-level preempts |
| `src/bridge/engine/rules/__init__.py` | Update — re-exports |
| `src/bridge/engine/sayc.py` | Create — wires all opening rules into a RuleRegistry |
| `tests/evaluate/test_hand_eval.py` | Update — tests for new evaluation functions |
| `tests/engine/rules/test_opening.py` | Create |
| `tests/engine/rules/test_opening_nt.py` | Create |
| `tests/engine/rules/test_opening_strong.py` | Create |
| `tests/engine/rules/test_opening_preempt.py` | Create |
| `tests/engine/test_sayc.py` | Create — integration smoke test |
| `tests/engine/rules/__init__.py` | Create — empty |

## Rule Design Pattern

Each rule is a class that extends the `Rule` ABC.

```python
class Open1NT(Rule):
    """Open 1NT with 15-17 HCP and balanced shape."""

    @property
    def name(self) -> str:
        return "opening.1nt"

    @property
    def category(self) -> Category:
        return Category.OPENING

    @property
    def priority(self) -> int:
        return 250  # Specific band: takes precedence over general 1-suit

    def applies(self, ctx: BiddingContext) -> bool:
        return 15 <= ctx.hcp <= 17 and ctx.is_balanced

    def select(self, ctx: BiddingContext) -> RuleResult:
        return RuleResult(
            bid=Bid.suit_bid(1, Strain.NOTRUMP),
            rule_name=self.name,
            explanation="15-17 HCP, balanced — SAYC 1NT opening",
        )
```

## Opening Bid Rules

### Priority Assignments

Higher priority = checked first. When a hand qualifies for multiple openings (e.g., 15 HCP balanced qualifies for both 1NT and 1-of-a-suit), the higher-priority rule wins.

| Priority | Rule | SAYC Reference |
|----------|------|----------------|
| 450 | `opening.2c` | 22+ HCP (or playing equivalent); strong, artificial, forcing |
| 270 | `opening.2nt` | 20-21 HCP, balanced |
| 250 | `opening.1nt` | 15-17 HCP, balanced |
| 200 | `opening.weak_two` | 5-11 HCP, 6-card suit, no void, no outside 4-card major |
| 180 | `opening.preempt_4` | Less than opening strength, 8+ card suit (4H/4S with 7+) |
| 170 | `opening.preempt_3` | Less than opening strength, 7-card suit |
| 130 | `opening.1_major` | 12-21 HCP, 5+ card major |
| 120 | `opening.1_minor` | 12-21 HCP, 3+ card minor |
| 50 | `opening.pass` | Fallback: pass when nothing else applies |

### Priority Rationale

- **2C (450)**: Highest — strong hands must never be underbid. Any hand with 22+ HCP opens 2C regardless of shape.
- **2NT (270) > 1NT (250)**: NT openings checked before suit openings because a balanced hand in the right HCP range should always open NT, not a suit. 2NT before 1NT because 20-21 must not fall through to 15-17.
- **Weak two (200)**: Above suit openings — a hand with 5-11 HCP and a 6-card suit should open weak, not pass. Above 1-suit because 1-suit requires 12+ HCP, so there's no overlap.
- **Preempts (170-180)**: Below weak twos (which are more specific) but above 1-suit (no overlap — preempts are below opening strength).
- **1-major (130) > 1-minor (120)**: When a hand has both a 5-card major and a biddable minor, the major is checked first. The rules themselves handle suit selection (longest suit, etc.).
- **Pass (50)**: Fallback — hands too weak to open.

## Rule Specifications

### `opening.2c` — Strong Artificial 2C

**SAYC**: "Strong, artificial 2C opening: 22+ HCP, or the playing equivalent with a very strong unbalanced hand."

```
applies: total_pts >= 22 (or hcp >= 22)
select:  Bid 2C
         forcing = True
         alerts = ("Artificial, strong, forcing",)
```

Implementation note: "playing equivalent" is subjective. For the deterministic engine, use `total_pts >= 22` (HCP + length points). This covers most cases. Extremely distributional hands (e.g., AKQJTxxxx in a suit with 16 HCP) are edge cases better handled by the LLM layer.

Also: hands with 22-24 balanced will match both 2C and potentially 2NT (20-21). Priority ensures 2C wins, which is correct — these hands open 2C and rebid 2NT.

### `opening.2nt` — 2NT Opening

**SAYC**: "20-21 HCP, balanced."

```
applies: 20 <= hcp <= 21 and is_balanced
select:  Bid 2NT
```

### `opening.1nt` — 1NT Opening

**SAYC**: "15-17 HCP, balanced. May contain a 5-card major or minor."

```
applies: 15 <= hcp <= 17 and is_balanced
select:  Bid 1NT
```

### `opening.weak_two` — Weak Two Opening (2D, 2H, 2S)

**SAYC**: "5-11 HCP, 6-card suit of reasonable quality. No void. No outside 4-card major."

```
applies:
  - 5 <= hcp <= 11
  - Has a 6-card suit (not clubs — 2C is reserved)
  - No void in any suit
  - No outside 4-card major (a major other than the 6-card suit)
  - Suit quality: 2 of {A, K, Q} or 3 of {A, K, Q, J, T} in the suit
select:
  - Bid 2 of the 6-card suit
  - If two 6-card suits (rare), bid the higher-ranking
```

Suit quality: The booklet says "reasonable quality" without precise definition. We use "2 of {A, K, Q} or 3 of {A, K, Q, J, T}" as the threshold.

### `opening.preempt_3` — 3-Level Preemptive Opening

**SAYC**: "7-card suit, too weak to open at the 1-level. Rule of 2 and 3."

```
applies:
  - hcp < 12 (below opening strength)
  - Has a 7-card suit
  - No outside 4-card major (common guideline)
  - Suit has reasonable quality (2 of {A,K,Q} or 3 of {A,K,Q,J,T})
select:
  - Bid 3 of the 7-card suit
```

The Rule of 2-3-4 (vulnerability-based trick guidelines) is hard to compute deterministically. For the initial implementation, use the simpler "less than opening strength + 7-card suit + quality" filter. Vulnerability adjustments can be added later.

### `opening.preempt_4` — 4-Level Preemptive Opening

**SAYC**: "8+ card suit (4H/4S may be 7+), less than opening strength."

```
applies:
  - hcp < 12
  - Has an 8+ card suit, OR has a 7+ card major
  - Suit has reasonable quality
select:
  - Bid 4 of the suit
```

### `opening.1_major` — 1-of-a-Major Opening (1H, 1S)

**SAYC**: "12-21 HCP, 5+ card major. Five-card majors required in all seats."

```
applies:
  - 12 <= hcp <= 21
  - Has a 5+ card major
  - NOT balanced with 15-17 HCP (those open 1NT)
  - NOT balanced with 20-21 HCP (those open 2NT)
  - hcp < 22 (those open 2C)
select:
  - If only one 5+ major: bid it
  - If two 5+ majors: bid the longer; if equal length, bid spades
```

Note: the `applies` exclusions for NT ranges are technically unnecessary because NT rules have higher priority. But they make the rule self-documenting and prevent the rule from appearing in the `candidates()` list alongside the correct NT opening.

### `opening.1_minor` — 1-of-a-Minor Opening (1C, 1D)

**SAYC**: "12-21 HCP. 1D requires 4+ cards (3 only with 4-4-3-2 shape: 4S-4H-3D-2C). 1C requires 3+ cards."

This is the most complex opening rule because of the suit selection logic:

```
applies:
  - 12 <= hcp <= 21
  - Does not qualify for 1-major (no 5+ card major)
  - NOT balanced with 15-17 HCP
  - NOT balanced with 20-21 HCP
  - hcp < 22
select:
  Suit selection priority:
  1. Longer minor → bid that minor
  2. 4-4 in minors → bid 1D
  3. 3-3 in minors → bid 1C
  4. 4-4-3-2 with 4S-4H-3D-2C → bid 1D (special case)
```

#### The 4-4-4-1 Shape

The SAYC booklet does not explicitly address 4-4-4-1 hands. The commonly taught guideline is "open the suit below the singleton." Our implementation derives this from the booklet's actual rules:

| Singleton | Reasoning | Open |
|-----------|-----------|------|
| Spade (4H-4D-4C) | Longest minor wins; if 4-4 minors, open 1D. But we also have 4H. Can't open 1H (need 5). So open 1D (4-4 minors rule). | 1D |
| Heart (4S-4D-4C) | Can't open 1S (need 5). 4-4 in minors → 1D. | 1D |
| Diamond (4S-4H-4C) | Can't open majors (need 5). Only 4C in minors. | 1C |
| Club (4S-4H-4D) | Can't open majors (need 5). Only 4D in minors. | 1D |

This matches the "suit below the singleton" teaching aid but is derived from SAYC's actual rules, not the teaching aid itself.

### `opening.pass` — Fallback Pass

```
applies: always True
select:  Pass
         explanation = "Hand does not meet opening requirements"
```

This is in the fallback priority band (50). It catches hands that don't qualify for any opening bid.

### Rule of 20 (1st/2nd Seat)

**SAYC**: "Add HCP + length of two longest suits. If >= 20, open."

This affects the `applies` logic of `opening.1_major` and `opening.1_minor`. A hand with 11 HCP and 5-4 shape (11 + 9 = 20) qualifies for opening. The standard "12-21 HCP" range should be relaxed to account for the Rule of 20.

Implementation: in `applies`, accept the hand if `hcp >= 12` OR if `hcp + len(longest) + len(second_longest) >= 20`.

### Rule of 15 (4th Seat)

**SAYC**: "HCP + number of spades >= 15."

In 4th seat, the Rule of 20 does not apply. Instead, use the Rule of 15. This requires checking `ctx.seat` position in the auction.

Implementation: this is a seat-dependent modifier on the opening rules. The cleanest approach is to have `opening.1_major` and `opening.1_minor` check the seat and apply the appropriate rule:
- 1st/2nd seat: Rule of 20
- 3rd seat: light openings permitted (use 12+ HCP or Rule of 20)
- 4th seat: Rule of 15

## Helper Functions

Several rules share suit-selection and hand-qualification logic. These are pure hand evaluation functions and belong in `evaluate/`, following the same pattern as `hcp()`, `quick_tricks()`, etc.

### New functions in `src/bridge/evaluate/hand_eval.py`

```python
def best_major(hand: Hand) -> Suit | None: ...  # Longest 5+ major, spades wins ties
def best_minor(hand: Hand) -> Suit: ...  # Minor suit selection per SAYC rules
def suit_quality(hand: Hand, suit: Suit) -> int: ...  # Count of top 5 honors in suit
def has_outside_four_card_major(hand: Hand, exclude: Suit) -> bool: ...
def rule_of_20(hand: Hand, hcp: int) -> bool: ...
def rule_of_15(hand: Hand, hcp: int) -> bool: ...
```

`opening_seat_position` needs auction context, not just a hand. It can live on `BiddingContext` or in the rule itself.

## SAYC Wiring (`sayc.py`)

```python
def create_sayc_registry() -> RuleRegistry:
    """Build a RuleRegistry with all SAYC opening rules."""
    reg = RuleRegistry()
    reg.register(Open2C())
    reg.register(Open2NT())
    reg.register(Open1NT())
    reg.register(OpenWeakTwo())
    reg.register(OpenPreempt3())
    reg.register(OpenPreempt4())
    reg.register(Open1Major())
    reg.register(Open1Minor())
    reg.register(OpenPass())
    return reg
```

As more phases are completed (response, rebid, etc.), this function grows to include all SAYC rules.

## Testing Strategy

### Correctness Verification

Every test hand must map to a specific SAYC guideline. Test names and comments cite the rule being verified.

```python
def test_1nt_15_hcp_balanced():
    """SAYC: 15-17 HCP balanced opens 1NT."""
    hand = Hand.from_pbn("AK32.KQ3.J84.A73")  # 17 HCP, 4-3-3-3
    ...
    assert result.bid == Bid.suit_bid(1, Strain.NOTRUMP)
    assert result.rule_name == "opening.1nt"
```

### Test Hands

Use a mix of textbook examples and edge cases. Each test file has a comment block listing the SAYC rule being tested.

#### `test_opening_nt.py`

| Hand | HCP | Shape | Expected | SAYC Rule |
|------|-----|-------|----------|-----------|
| `AK32.KQ3.J84.A73` | 17 | 4-3-3-3 | 1NT | 15-17 balanced |
| `AQ3.KJ84.QJ3.K84` | 15 | 3-4-3-3 | 1NT | 15-17 balanced |
| `AKJ52.KQ3.84.A73` | 17 | 5-3-2-3 | 1NT | 5-3-3-2 is balanced; 5-card major OK |
| `AQ3.K84.AKJT3.Q4` | 17 | 3-3-5-2 | 1NT | 5-card minor OK |
| `AKQ3.KJ8.AQ3.J84` | 20 | 4-3-3-3 | 2NT | 20-21 balanced |
| `AKQJ.KQ3.AJ8.Q84` | 21 | 4-3-3-3 | 2NT | 20-21 balanced |
| `AQ32.KJ8.A84.K73` | 14 | 4-3-3-3 | NOT 1NT | 14 HCP too low |
| `AKQ3.KQJ.AJ8.A84` | 23 | 4-3-3-3 | 2C (not NT) | 22+ opens 2C |

#### `test_opening.py` (1-level suits)

| Hand | HCP | Shape | Expected | SAYC Rule |
|------|-----|-------|----------|-----------|
| `AKJ52.Q73.84.A73` | 14 | 5-3-2-3 | 1S | 5-card major |
| `84.AKJ52.Q73.A73` | 14 | 2-5-3-3 | 1H | 5-card major |
| `AKJ52.AQT73.8.73` | 15 | 5-5-1-2 | 1S | Two 5-card suits: higher ranking |
| `K873.A2.KJ84.Q73` | 13 | 4-2-4-3 | 1D | No 5-card major; longer minor |
| `K873.A2.Q73.KJ84` | 13 | 4-2-3-4 | 1C | No 5-card major; longer minor |
| `K873.A2.KJ84.Q74` | 13 | 4-2-4-3 | 1D | 4-4 minors: open 1D |
| `KQ73.A2.Q74.KJ84` | 13 | 4-2-3-4 | 1D? | 4-2-3-4: only 3D, so 1C? This needs careful analysis |
| `K873.K92.KJ8.A84` | 13 | 4-3-3-3 | 1C | 3-3 minors: open 1C |
| `KQ73.A2.KJ84.Q74` | 13 | 4-2-4-3 | 1D | 4-4 minors → 1D |
| `AKJ8.9.AJ84.Q742` | 13 | 4-1-4-4 | 1D | 4-4-4-1 singleton heart → 1D |
| `9.AKJ8.AJ84.Q742` | 13 | 1-4-4-4 | 1C | 4-4-4-1 singleton spade → 1C (or 1D?) |

#### `test_opening_strong.py`

| Hand | HCP | Shape | Expected | SAYC Rule |
|------|-----|-------|----------|-----------|
| `AKQJ.AKQ.AJ8.A84` | 26 | 4-3-3-3 | 2C | 22+ HCP |
| `AKQJT.AKQ.AK8.84` | 24 | 5-3-3-2 | 2C | 22+ balanced → 2C (rebid 2NT) |
| `AKQ.K3.AKQJT84.4` | 22 | 3-2-7-1 | 2C | 22+ HCP unbalanced |

#### `test_opening_preempt.py`

| Hand | HCP | Shape | Expected | SAYC Rule |
|------|-----|-------|----------|-----------|
| `84.KQJ842.73.J84` | 7 | 2-6-2-3 | 2H | Weak two: 6-card suit, 5-11 HCP |
| `KQT973.84.73.J84` | 7 | 6-2-2-3 | 2S | Weak two: 6-card suit |
| `84.73.KQJ842.J84` | 7 | 2-2-6-3 | 2D | Weak two: 6-card suit |
| `84.73.J84.KQJ842` | 7 | 2-2-3-6 | Pass | Can't open weak 2C (reserved) |
| `84.KQT9732.73.84` | 5 | 2-7-2-2 | 3H | 7-card suit, preempt |
| `K4.QJT8432.73.84` | 6 | 2-7-2-2 | 3H | 7-card suit, preempt |
| `84.AKJ52.Q73.J84` | 11 | 2-5-3-3 | Pass | Only 5-card suit, doesn't meet weak two or preempt |
| `84.KQJ842.A3.J84` | 10 | 2-6-2-3 | 1H? or 2H? | 10 HCP with 6-card suit — borderline. Rule of 20 says 10+8=18, too low. Open weak 2H. |

### Edge Cases

- 18 HCP balanced: should open 1-of-a-suit (not 1NT, not 2NT). Rebids 2NT in Phase 6.
- 22 HCP balanced: should open 2C (not 2NT). Rebids 2NT in Phase 6.
- 4th seat with 11 HCP and 2 spades: Rule of 15 = 13, should pass.
- 4th seat with 11 HCP and 4 spades: Rule of 15 = 15, should open.
- Hand meeting Rule of 20 but only 11 HCP: should open in 1st/2nd seat.

### Integration Test (`test_sayc.py`)

Smoke test that wires `create_sayc_registry()` with `BidSelector` and runs a few hands through the full pipeline:

```python
def test_balanced_17_opens_1nt():
    reg = create_sayc_registry()
    selector = BidSelector(reg)
    board = Board(hand=Hand.from_pbn("AK32.KQ3.J84.A73"), seat=Seat.NORTH, auction=AuctionState(dealer=Seat.NORTH))
    ctx = BiddingContext(board)
    result = selector.select(ctx)
    assert result.rule_name == "opening.1nt"
```

## Implementation Order

1. `_opening_helpers.py` — shared suit selection and qualification helpers
2. `opening_nt.py` — 1NT, 2NT rules (simplest: just HCP + balanced check)
3. `opening_strong.py` — 2C rule
4. `opening_preempt.py` — weak twos, 3-level, 4-level preempts
5. `opening.py` — 1-level suit openings (most complex: suit selection logic)
6. `sayc.py` — wire everything into a registry
7. `rules/__init__.py` — re-exports
8. Tests for each module
9. Integration smoke test
10. `pdm run check`

## Verification

```bash
pdm run test tests/engine/rules/
pdm run test tests/engine/test_sayc.py
pdm run check
```

## Open Questions

1. ~~**Rule of 20 threshold**~~: **Resolved** — use `hcp >= 12 OR rule_of_20`. The booklet says Rule of 20 is for "borderline" hands; 12+ HCP hands open regardless.

2. ~~**3NT opening**~~: **Resolved** — omit entirely. A 25-27 balanced hand opens 2C; the 3NT bid comes as a rebid in Phase 6.

3. ~~**Weak two suit quality**~~: **Resolved** — require 2 of {A, K, Q} or 3 of {A, K, Q, J, T}. The booklet says "reasonable quality" without a precise definition; this threshold is a practical implementation.

4. ~~**4-4-4-1 singleton spade**~~: **Resolved** — open 1D, derived from "4-4 in minors → open 1D." The "middle suit" teaching aid suggests 1H, but that violates five-card majors. Note the discrepancy in a comment.
