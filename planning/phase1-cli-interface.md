# Phase 1: CLI Interface — Detailed Implementation Plan

## Overview

Interactive terminal application using typer + rich (already dependencies). Two commands:
- `bridge advise` — single-shot bid recommendation
- `bridge practice` — interactive solo practice loop

Before building the CLI, we first refactor the rule engine to use declarative conditions (Step 0). This enables structured thought-process generation — each condition can explain why it passed or failed, giving the user a clear trace of the engine's reasoning.

The CLI validates the full advisor UX and provides a usable solo practice tool. No multiplayer (that needs a server in Phase 2).

---

## Dependencies

Already in `pyproject.toml`:
- `typer>=0.9` — CLI framework
- `rich>=13.0` — terminal formatting (tables, panels, colors)

Already wired in `pyproject.toml`:
```toml
[project.scripts]
bridge = "bridge.cli.app:app"
```

No new dependencies needed.

---

## Files to Create/Modify

### Step 0 (Condition System)
```
src/bridge/engine/
    condition.py                    # NEW — Condition base types, combinators, concrete conditions
    rule.py                         # MODIFY — add conditions property + check() method
    selector.py                     # MODIFY — add think() method
    rules/sayc/opening/suit.py      # MODIFY — migrate to conditions
    rules/sayc/opening/nt.py        # MODIFY
    rules/sayc/opening/strong.py    # MODIFY
    rules/sayc/opening/preempt.py   # MODIFY
    rules/sayc/response/suit.py     # MODIFY
    rules/sayc/response/nt.py       # MODIFY
    rules/sayc/response/strong.py   # MODIFY
    rules/sayc/response/preempt.py  # MODIFY
    rules/sayc/rebid/suit.py        # MODIFY
    rules/sayc/rebid/nt.py          # MODIFY
    rules/sayc/rebid/strong.py      # MODIFY
    rules/sayc/rebid/preempt.py     # MODIFY
tests/engine/
    test_condition.py               # NEW — condition unit tests
src/bridge/service/
    models.py                       # MODIFY — add ThoughtProcess to BiddingAdvice
    advisor.py                      # MODIFY — call think()
```

### Steps 1-5 (CLI)
```
src/bridge/cli/
    app.py              # NEW — Typer commands (advise, practice)
    display.py          # NEW — Rich output formatting
tests/cli/
    __init__.py         # NEW
    test_display.py     # NEW — formatting unit tests
    test_app.py         # NEW — CLI integration tests
```

---

## Step 0: Declarative Condition System

### Motivation

The 126 SAYC rules have imperative `applies()` methods — opaque code that returns True/False. To generate thought-process explanations, we need rules to be introspectable: each condition should describe *why* it passed or failed for a given hand. This refactor replaces `applies()` with declarative condition objects across all 126 rules.

### Code Quality Note

All code in Step 0 (condition.py, rule.py updates, and migrated rules) should be well documented with explanatory comments. This is new infrastructure that future rule authors need to understand — comment the "why" behind design decisions, explain non-obvious patterns (Computed caching, Not label semantics, All short-circuiting), and include usage examples in docstrings.

### Step 0A: Condition Infrastructure (`src/bridge/engine/condition.py`)

#### Base Types

```python
@dataclass(frozen=True)
class ConditionResult:
    """The outcome of evaluating a single condition."""
    passed: bool
    label: str    # Static: "15-17 HCP"
    detail: str   # Contextual: "You have 16 HCP (in the 15-17 range)"

@dataclass(frozen=True)
class CheckResult:
    """Aggregate result from evaluating all conditions on a rule."""
    passed: bool
    results: tuple[ConditionResult, ...]
    computed: dict[str, Any]   # Named values from Computed conditions

class Condition(ABC):
    """A single testable predicate about the hand and auction state."""
    @abstractmethod
    def check(self, ctx: BiddingContext) -> ConditionResult: ...
    @property
    @abstractmethod
    def label(self) -> str: ...
```

#### Combinators

**`All(*conditions)`** — AND logic. Used by ~95% of rules. Has `check_all(ctx) -> CheckResult` that collects individual results and computed values. Short-circuits on first failure.

**`Any(*paths)`** — OR logic. Used by ~6 rules (Stayman, Rebid3NTAfterRaiseMinor, etc.). Each path is typically an `All(...)`. Tries each path in order; returns the first passing path's `CheckResult`.

**`Not(inner, label=None)`** — Negation. Optional label for clearer thought-process text. Without a label, uses the inner condition's label. With a label, provides human-readable context:
```python
Not(has_5_plus_major)
# Pass: "No 5+ card major"
# Fail: "Has 5+ card major"

Not(All(Balanced(strict=True), HcpRange(15, 17)), label="in 1NT range")
# Pass: "Not in 1NT range"
# Fail: "In 1NT range (balanced, 16 HCP)"
```

#### Computed Condition

Solves the shared state problem between `applies()` and `select()`. About 30 rules call a suit-finding function in `applies()` to check if a result exists, then re-call it in `select()` to use the result.

```python
class Computed(Condition, Generic[T]):
    """Compute a value, cache it, and pass/fail based on None.

    The function receives a BiddingContext and returns T | None.
    - If the result is not None: condition passes, value is cached.
    - If the result is None: condition fails.

    select() reads the cached value via .value after conditions pass.
    Each check() call overwrites the cache, so the value is always
    fresh for the current hand.
    """

    def __init__(
        self,
        func: Callable[[BiddingContext], T | None],
        label_text: str,
    ) -> None:
        self._func = func
        self._label_text = label_text
        self._cached: T | None = None

    @property
    def label(self) -> str:
        return self._label_text

    def check(self, ctx: BiddingContext) -> ConditionResult:
        result = self._func(ctx)
        self._cached = result
        if result is not None:
            return ConditionResult(
                passed=True,
                label=self._label_text,
                detail=f"Found {result} ({self._label_text})",
            )
        return ConditionResult(
            passed=False,
            label=self._label_text,
            detail=f"No {self._label_text} found",
        )

    @property
    def value(self) -> T:
        """Returns cached value from last check(). Asserts non-None."""
        assert self._cached is not None
        return self._cached
```

Rules store `Computed` instances as attributes so `select()` can read the cached value:

```python
class RespondNewSuit1Level(Rule):
    def __init__(self) -> None:
        self._find_suit = Computed(_find_new_suit_1_level, "4+ card suit at 1-level")

    @property
    def conditions(self) -> Condition:
        return All(opened_1_suit, HcpRange(min_hcp=6), self._find_suit)

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._find_suit.value  # Cached from conditions check
        return RuleResult(bid=SuitBid(1, suit), ...)
```

Thread safety: `Computed` stores mutable state on the instance. Rules are singletons evaluated sequentially by `BidSelector` — this is safe for single-threaded use.

#### Concrete Condition Classes

| Class | Purpose | Example |
|-------|---------|---------|
| `HcpRange(min, max)` | HCP in range | `HcpRange(15, 17)` |
| `TotalPtsRange(min, max)` | Total points in range | `TotalPtsRange(min_pts=22)` |
| `BergenPtsRange(min, max)` | Bergen points in range | Opener rebids after major raise |
| `SupportPtsRange(min, max)` | Support points in range | Responder raises |
| `Balanced(strict=False)` | Balanced or semi-balanced | `strict=True` for 1NT/2NT |
| `NoVoid()` | No zero-length suit | Weak two requirement |
| `ShapeNot(pattern)` | Sorted shape != tuple | `ShapeNot((4, 3, 3, 3))` |
| `SuitLength(suit, min, max)` | Specific suit length | `SuitLength(Suit.HEARTS, min_len=4)` |
| `HasSuitFit(suit_fn, min_len)` | Dynamic suit from auction | Support for opener's suit |
| `MeetsOpeningStrength()` | 12+/Rule of 20/Rule of 15 | Opening rules |
| `@condition(label)` | Decorator: turns a bool function into a Condition | `@condition("partner opened 1NT")` |
| `Computed(func, label)` | Compute + cache value | Suit-finding functions |
| `All(*conditions)` | AND combinator | Most rules |
| `Any(*paths)` | OR combinator | Stayman, branching rebids |
| `Not(inner, label=None)` | Negation (optional label) | `Not(has_5_plus_major)`, `Not(..., label="in 1NT range")` |

#### `@condition` Decorator

Turns a `(BiddingContext) -> bool` function into a `Condition` object. This replaces the ~35 existing boolean helper functions (e.g., `_opened_1nt`, `_partner_single_raised`) — instead of writing a private function and wrapping it separately, the decorator makes the function itself a Condition.

```python
class _PredicateCondition(Condition):
    """A Condition created by the @condition decorator.

    Wraps a (BiddingContext -> bool) function, making it both:
    - A Condition (usable in All/Any/Not combinators)
    - A callable (usable by other helper functions that need the bool result)

    The __call__ method allows decorated functions to still be called
    as regular functions by other helpers that compose on top of them.
    """

    def __init__(self, func: Callable[[BiddingContext], bool], label_text: str) -> None:
        self._func = func
        self._label_text = label_text

    @property
    def label(self) -> str:
        return self._label_text

    def check(self, ctx: BiddingContext) -> ConditionResult:
        passed = self._func(ctx)
        if passed:
            return ConditionResult(
                passed=True,
                label=self._label_text,
                detail=self._label_text,
            )
        return ConditionResult(
            passed=False,
            label=self._label_text,
            detail=f"Not: {self._label_text}",
        )

    def __call__(self, ctx: BiddingContext) -> bool:
        """Allow this condition to be called as a regular function.

        This is needed because some decorated helpers call other
        decorated helpers as part of their logic:

            @condition("partner bid new suit at 1-level")
            def partner_bid_new_suit_1_level(ctx):
                return partner_bid_new_suit(ctx) and ...
                       ^^^^^^^^^^^^^^^^^^^^^^
                       calls another @condition as a function
        """
        return self._func(ctx)


def condition(label: str) -> Callable[[Callable[[BiddingContext], bool]], _PredicateCondition]:
    """Decorator that turns a (BiddingContext -> bool) function into a Condition.

    Usage:
        @condition("partner opened 1NT")
        def opened_1nt(ctx: BiddingContext) -> bool:
            if ctx.opening_bid is None:
                return False
            _, bid = ctx.opening_bid
            return is_suit_bid(bid) and bid.level == 1 and bid.suit == Suit.NOTRUMP

    The decorated function is now a Condition object that can be used
    directly in All/Any/Not, AND can still be called as a function:

        # As a condition in a rule:
        All(opened_1nt, HcpRange(8, 10))

        # As a function in another helper:
        opened_1nt(ctx)  # returns bool
    """
    def decorator(func: Callable[[BiddingContext], bool]) -> _PredicateCondition:
        return _PredicateCondition(func, label)
    return decorator
```

**Usage in rule files** — each helper becomes a single decorated function:

```python
# Before (two steps: private function + wrapper):
def _opened_1_suit(ctx: BiddingContext) -> bool:
    bid = _opening_bid(ctx)
    return is_suit_bid(bid) and bid.level == 1

opened_1_suit = AuctionIs(_opened_1_suit, "partner opened 1 of a suit")

# After (one step: decorated function IS the condition):
@condition("partner opened 1 of a suit")
def opened_1_suit(ctx: BiddingContext) -> bool:
    bid = _opening_bid(ctx)
    return is_suit_bid(bid) and bid.level == 1
```

**Helpers that call other helpers** — works because `__call__` delegates to the original function:

```python
@condition("partner bid a new suit")
def partner_bid_new_suit(ctx: BiddingContext) -> bool:
    resp = _partner_response(ctx)
    return resp.suit != _my_opening_bid(ctx).suit

@condition("partner bid new suit at 1-level")
def partner_bid_new_suit_1_level(ctx: BiddingContext) -> bool:
    # Calls partner_bid_new_suit as a function (via __call__),
    # even though it's also a Condition object
    return partner_bid_new_suit(ctx) and _partner_response(ctx).level == 1
```

**Which functions get `@condition`**: Only the ~35 boolean helpers that appear directly in rule conditions. Internal utility functions that return values (like `_opening_bid(ctx) -> SuitBid`, `_partner_response(ctx) -> SuitBid`) stay as plain functions — they're not conditions, they're just helpers.

#### Condition Descriptions

Each condition generates contextual text for the thought process. The `detail` field includes actual values from the hand for rich explanations. Below are exact strings the implementations would produce:

| Condition | Passed detail | Failed detail |
|-----------|---------------|---------------|
| `HcpRange(15, 17)` | `"16 HCP (15-17)"` | `"12 HCP (need 15-17)"` |
| `TotalPtsRange(min_pts=22)` | `"23 total points (22+)"` | `"19 total points (need 22+)"` |
| `Balanced(strict=True)` | `"Shape 4-3-3-3 (balanced)"` | `"Shape 5-4-3-1 (not balanced)"` |
| `NoVoid()` | `"No void"` | `"Has void"` |
| `SuitLength(HEARTS, min_len=4)` | `"5 hearts (4+ required)"` | `"2 hearts (4+ required)"` |
| `Computed(fn, "4+ card suit at 1-level")` | `"Found spades (4+ card suit at 1-level)"` | `"No 4+ card suit at 1-level found"` |
| `@condition("partner opened 1NT")` | `"Partner opened 1NT"` | `"Not: partner opened 1NT"` |
| `Not(has_5_plus_major)` | `"No 5+ card major"` (inner failed) | `"Has 5+ card major"` (inner passed) |
| `Not(..., label="in 1NT range")` | `"Not in 1NT range"` | `"In 1NT range"` |

Notes:
- Named classes (HcpRange, Balanced, etc.) pull actual values from `ctx` to produce contextual details
- `@condition` uses the label directly — capitalize labels for readability (e.g., `"Partner opened 1NT"` not `"partner opened 1NT"`)
- `Computed` detail on pass uses `f"Found {result} ({label})"` — result's `__str__` must be human-readable
- `Not` with no label auto-generates from inner: prepends "No " on pass, strips "No " on fail
- `Not` with a label uses it directly: `"Not {label}"` on pass, `"In {label}"` on fail

#### Tests: `tests/engine/test_condition.py`

- Test each concrete condition class with pass/fail cases
- Test `All` short-circuits on first failure, collects results
- Test `Any` tries paths in order, returns first match
- Test `Not` with and without label produces correct pass/fail
- Test `Computed` caches value and makes it available via `.value`
- Test `@condition` decorator creates a Condition that is also callable as a function
- Test `@condition` decorated functions can call each other via `__call__`

---

### Step 0B: Update Rule Base Class (`src/bridge/engine/rule.py`)

Add optional `conditions` property (returns `None` by default). Add `check()` method. Existing rules keep working — they override `applies()` and don't define `conditions`.

```python
class Rule(ABC):
    # ... existing name, category, priority, select ...

    @property
    def conditions(self) -> Condition | None:
        """Override to provide declarative conditions."""
        return None

    def applies(self, ctx: BiddingContext) -> bool:
        conds = self.conditions
        if conds is not None:
            return self.check(ctx).passed
        raise NotImplementedError  # Subclass must override

    def check(self, ctx: BiddingContext) -> CheckResult:
        """Full condition evaluation with individual results."""
        conds = self.conditions
        if conds is None:
            # Legacy rule without conditions — minimal CheckResult
            passed = self.applies(ctx)
            return CheckResult(passed=passed, results=(), computed={})
        if isinstance(conds, (All, Any)):
            return conds.check_all(ctx)
        r = conds.check(ctx)
        return CheckResult(passed=r.passed, results=(r,), computed={})
```

**Zero breakage**: existing rules don't define `conditions`, so they hit the `NotImplementedError` path, which they avoid by overriding `applies()` directly. As rules are migrated, they define `conditions` and stop overriding `applies()`.

---

### Step 0C: Migrate Opening Rules (~10 rules)

**Files**: `opening/nt.py`, `strong.py`, `suit.py`, `preempt.py`

Start with the simplest rules to prove the pattern:

```python
# Open1NT — simplest possible rule
class Open1NT(Rule):
    @property
    def conditions(self) -> Condition:
        return All(HcpRange(15, 17), Balanced(strict=True))

# Open1Major — demonstrates Not (with label) + Computed
class Open1Major(Rule):
    def __init__(self) -> None:
        self._best_major = Computed(_best_major_from_ctx, "5+ card major")

    @property
    def conditions(self) -> Condition:
        return All(
            MeetsOpeningStrength(),
            Not(All(Balanced(strict=True), HcpRange(15, 17)), label="in 1NT range"),
            Not(All(Balanced(strict=True), HcpRange(20, 21)), label="in 2NT range"),
            Not(TotalPtsRange(min_pts=22), label="in 2C range"),
            self._best_major,
        )

    def select(self, ctx: BiddingContext) -> RuleResult:
        suit = self._best_major.value
        ...

# OpenWeakTwo — demonstrates NoVoid + Computed with instance method
class OpenWeakTwo(Rule):
    def __init__(self) -> None:
        self._find_suit = Computed(self._find_weak_two_suit, "6-card quality suit")

    @property
    def conditions(self) -> Condition:
        return All(HcpRange(5, 11), NoVoid(), self._find_suit)

# OpenPass — always applies, no conditions needed
class OpenPass(Rule):
    def applies(self, ctx: BiddingContext) -> bool:
        return True  # Keep as-is: no meaningful conditions to declare
```

All existing opening tests must pass unchanged.

---

### Step 0D: Migrate Response Rules (~50 rules)

**Files**: `response/suit.py`, `nt.py`, `strong.py`, `preempt.py`

Key patterns demonstrated:

**Pure AND (most rules)**:
```python
class RespondSingleRaiseMajor(Rule):
    @property
    def conditions(self) -> Condition:
        return All(
            opened_1_major,
            HasSuitFit(_opener_suit, min_len=3),
            SupportPtsRange(min_pts=6, max_pts=10),
        )
```

**OR logic (RespondStayman)**:
```python
class RespondStayman(Rule):
    @property
    def conditions(self) -> Condition:
        return All(
            opened_1nt,
            Any(
                # Garbage Stayman: 4-4+ in majors, any HCP
                All(SuitLength(Suit.HEARTS, min_len=4), SuitLength(Suit.SPADES, min_len=4)),
                # Regular Stayman: 8+ HCP, 4-card major, no 5+ major, not 4333
                All(
                    HcpRange(min_hcp=8),
                    has_4_card_major,
                    Not(has_5_plus_major),
                    ShapeNot((4, 3, 3, 3)),
                ),
            ),
        )
```

**Computed for suit-finding**:
```python
class RespondJumpShift(Rule):
    def __init__(self) -> None:
        self._find_suit = Computed(_find_jump_shift_suit, "strong suit for jump shift")

    @property
    def conditions(self) -> Condition:
        return All(opened_1_suit, HcpRange(min_hcp=17), self._find_suit)
```

---

### Step 0E: Migrate Rebid Rules (~65 rules)

**Files**: `rebid/suit.py`, `nt.py`, `strong.py`, `preempt.py`

Largest batch. Key patterns:

- Heavy use of `Computed` for suit-finding (`_find_new_suit_for_rebid`, `_find_reverse_suit`, `_find_help_suit`, `_find_shortness_suit`, etc.)
- `BergenPtsRange` for opener rebids after major raises
- `Rebid3NTAfterRaiseMinor` uses `Any` (two paths: single raise 18-19 HCP, limit raise 12+ HCP)
- `RebidSuitAfterPositive2C` uses `Any` (after suit response vs after 2NT)
- Jacoby rebids use cascading `Not` for shortness/side-suit priority
- Most 1NT rebid rules (Stayman completions, transfer completions) are pure AND with `@condition`-decorated helpers

---

### Step 0F: Thought Process on BidSelector (`src/bridge/engine/selector.py`)

Add `think()` method and supporting types:

```python
@dataclass(frozen=True)
class ThoughtStep:
    """One rule evaluated during the thought process."""
    rule_name: str
    bid: Bid
    explanation: str
    passed: bool
    condition_results: tuple[ConditionResult, ...]

@dataclass(frozen=True)
class ThoughtProcess:
    """Full trace of how the engine reached its decision."""
    steps: tuple[ThoughtStep, ...]
    selected_rule: str
```

```python
class BidSelector:
    def think(self, ctx: BiddingContext) -> ThoughtProcess:
        """Evaluate all candidate rules and produce a structured trace."""
        rules = self._collect_rules(ctx)
        steps: list[ThoughtStep] = []
        selected: str = "fallback.pass"

        for rule in rules:
            check_result = rule.check(ctx)
            result = rule.select(ctx) if check_result.passed else RuleResult(...)
            steps.append(ThoughtStep(
                rule_name=rule.name,
                bid=result.bid,
                explanation=result.explanation,
                passed=check_result.passed,
                condition_results=check_result.results,
            ))
            if check_result.passed and selected == "fallback.pass":
                selected = rule.name

        return ThoughtProcess(steps=tuple(steps), selected_rule=selected)
```

The existing `select()` and `candidates()` methods stay unchanged.

**Tests**: Add to `tests/engine/test_selector.py` — test `think()` returns structured trace with condition results.

---

### Step 0G: Update BiddingAdvisor + BiddingAdvice

**Modify**: `src/bridge/service/models.py` — add `thought_process: ThoughtProcess` field to `BiddingAdvice`.

**Modify**: `src/bridge/service/advisor.py` — call `self._selector.think(ctx)` and include in `BiddingAdvice`.

This replaces the template-based `thought_process.py` that was originally planned. The condition system makes it unnecessary — thought process comes directly from condition evaluation results.

---

### Step 0 Implementation Order

1. **0A**: `condition.py` — all base types, combinators, concrete conditions + tests
2. **0B**: `rule.py` — add `conditions` property + `check()` method
3. **0C**: Opening rules migration (~10 rules) — prove the pattern
4. **0D**: Response rules migration (~50 rules)
5. **0E**: Rebid rules migration (~65 rules)
6. **0F**: `selector.py` — add `think()` method + tests
7. **0G**: `advisor.py` + `models.py` — wire thought process into BiddingAdvice

Steps 0A and 0B are prerequisites. 0C-0E are independent per file (can be done in any order). 0F-0G depend on having at least some rules migrated.

### Step 0 Verification

After each sub-step:
- `pdm run check` passes (all 946+ tests, lint, typecheck)
- No existing test assertions changed

After full Step 0:
- Every rule (except fallback Pass rules) has a `conditions` property
- `BidSelector.think()` produces a structured trace for any hand
- `BiddingAdvice` includes `thought_process` field
- Manual check: 16 HCP balanced hand shows Open1NT matching with "You have 16 HCP (in the 15-17 range)" and "Shape is 4-3-3-2 (balanced)"

---

## Step 1: Display Module (`src/bridge/cli/display.py`)

Pure formatting functions that take domain objects and return Rich renderables. No I/O — these just build Rich objects. This makes them testable and reusable.

### Functions

#### `format_hand(hand: Hand) -> Panel`

Display a hand with suit symbols and rank characters, inside a Rich Panel.

```
--- Your Hand ----------------------------
  ♠  A K J 5 2
  ♥  K Q 3
  ♦  8 4
  ♣  A 7 3
---------------------------------------------
```

Uses `hand.suit_cards(suit)` for each suit in SHDC order. Suit symbols from `Suit.__str__()` (♠♥♦♣). Cards space-separated, high to low.

Color the suit symbols: spades blue, hearts red, diamonds orange (or yellow), clubs green. Use Rich markup: `[red]♥[/red]`.

#### `format_hand_eval(eval: HandEvaluation) -> Panel`

```
--- Hand Evaluation ----------------------
  HCP: 15   Total Pts: 16
  Shape: 5-3-2-3 (semi-balanced)
  Quick Tricks: 3.5   Losers: 6
  Controls: 6
---------------------------------------------
```

Derives shape string from `eval.shape` (e.g., "5-3-2-3"). Shows "balanced", "semi-balanced", or nothing based on flags. Combine HCP + total on one line. Quick tricks, losers, controls on subsequent lines.

#### `format_auction(bids: list[tuple[Seat, Bid]], dealer: Seat, current_seat: Seat) -> Panel`

4-column auction grid with seat headers. Highlights whose turn it is with `[bold]?[/bold]` or a marker.

```
--- Auction ------------------------------
  W     N     E     S
              1♥   Pass
  ?
---------------------------------------------
```

Column order: always W, N, E, S (standard bridge diagram). Bids fill left-to-right starting from the dealer's column. Empty cells before the dealer in the first row.

Use suit symbols with colors in bid display: "1♥" not "1H".

#### `format_advice(advice: BiddingAdvice) -> Panel`

```
--- Recommended Bid: 1♠ -----------------
  5+ spades, new suit at 1-level (forcing)
  SAYC: new suit response at 1-level
---------------------------------------------
```

Shows `advice.recommended.bid` (formatted with suit symbol), `advice.recommended.explanation`. If `advice.recommended.forcing`, append "(forcing)" indicator.

#### `format_alternatives(alternatives: list[RuleResult]) -> Panel`

```
--- Alternatives -------------------------
  2♥  - Single raise (3+ support, 6-10 pts)
  2NT - 13-15 HCP balanced, no 4-card major
---------------------------------------------
```

Each alternative on one line: bid (formatted), dash, explanation. Skip if empty list.

#### `format_thought_process(thought_process: ThoughtProcess) -> Panel`

Renders the structured `ThoughtProcess` from the condition system. Shows:
1. The winning rule and why it matched (all passing conditions)
2. Key alternatives that were considered and the first condition that failed

```
--- Thought Process ----------------------
  Recommended: 1♠ (response.new_suit_1_level)
    ✓ Partner opened 1 of a suit
    ✓ You have 15 HCP (6+ required)
    ✓ Found spades (4+ card suit at 1-level)

  Also considered:
    2♥ (response.single_raise_major)
      ✗ You have 15 HCP (above the 10 maximum)
    2NT (response.2nt_balanced)
      ✗ You have 5 spades (need no 4-card major)
---------------------------------------------
```

#### `format_contract(contract: Contract) -> str`

Formats: "1♥ by North", "3NT by South doubled", "Passed out". Uses suit symbols.

#### `format_bid_prompt(current_seat: Seat) -> str`

Returns prompt string like "North's bid: " for use with `rich.prompt.Prompt`.

### Implementation Notes

- All `format_*` functions return Rich renderables (Panel, Table, Text) or plain strings
- Use `rich.panel.Panel` for boxed sections
- Use `rich.table.Table` for the auction grid
- Use `rich.text.Text` for colored suit symbols
- Helper: `format_bid(bid: Bid) -> str` to convert a Bid to display string with suit symbols (e.g., SuitBid(1, HEARTS) -> "1♥")

---

## Step 2: CLI App (`src/bridge/cli/app.py`)

### Command: `bridge advise`

Single-shot mode. Takes a hand and optional auction, returns advice.

```bash
bridge advise --hand "AKJ52.KQ3.84.A73"
bridge advise --hand "AKJ52.KQ3.84.A73" --auction "1H P"
bridge advise --hand "AKJ52.KQ3.84.A73" --auction "1H P" --dealer E
bridge advise --hand "AKJ52.KQ3.84.A73" --auction "1H P" --vulnerability NS
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--hand` | str | required | Hand in PBN format (AKJ52.KQ3.84.A73) |
| `--auction` | str | "" | Space-separated bids so far (e.g., "1H P") |
| `--dealer` | str | "N" | Dealer seat (N/E/S/W) |
| `--vulnerability` | str | "None" | Vulnerability (None/NS/EW/Both) |

#### Flow

1. Parse hand via `Hand.from_pbn(hand_str)` — error message if invalid
2. Parse auction via `parse_auction(auction_str, dealer, vulnerability)` — error message if invalid
3. Create `BiddingAdvisor`, call `advise(hand, auction)`
4. Print using display functions:
   - `format_hand(hand)`
   - `format_hand_eval(advice.hand_evaluation)`
   - `format_auction(auction.bids, dealer, auction.current_seat)`
   - `format_advice(advice)`
   - `format_thought_process(advice.thought_process)`
   - `format_alternatives(advice.alternatives)`

#### Error Handling

- Invalid hand format: friendly error with example format
- Invalid bid in auction: friendly error with valid bid examples
- Illegal bid sequence: show what went wrong

Use `rich.console.Console` for error output with `console.print("[red]Error:[/red] ...")`.

### Command: `bridge practice`

Interactive solo practice loop.

```bash
bridge practice
bridge practice --seat N
bridge practice --dealer E --vulnerability NS
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--seat` | str | "N" | Your seat (N/E/S/W) |
| `--dealer` | str | "N" | Dealer seat |
| `--vulnerability` | str | "None" | Vulnerability |

#### Flow

1. Deal random hands via `deal()`
2. Show your hand via `format_hand()`
3. Show hand evaluation via `format_hand_eval()`
4. Enter practice loop:
   a. Show current auction state via `format_auction()`
   b. If it's a computer seat's turn:
      - Use `BiddingAdvisor.advise()` to get the computer's bid
      - Make the bid, show it: "East bids: Pass"
      - Continue to next seat
   c. If it's your turn:
      - Prompt for your bid (or type "help" / "advise" / "quit")
      - If "advise": show full advice + thought process, then re-prompt
      - Parse the bid via `parse_bid()`
      - Compare to engine recommendation
      - If match: "Correct! That matches the engine's recommendation."
      - If different: "The engine recommends {bid}: {explanation}. Your bid {bid} was also recorded."
      - Record the player's actual bid (not the engine's) to continue the auction
   d. If auction is complete:
      - Show final contract via `format_contract()`
      - Ask "Play again? [Y/n]"
      - If yes: deal new hands, restart
      - If no: exit

#### Computer Bidding

Computer seats use `BiddingAdvisor.advise()` for their bids. The advisor falls back to Pass when no rule applies, which is the expected behavior for now (no competitive bidding rules yet).

The computer uses the full hand for its seat (from the deal). The human player's hand is shown to them, but other hands are hidden.

#### Bid Input

Accept the same formats as `parse_bid()`: "1H", "P", "Pass", "X", "XX", "3NT", etc. Case-insensitive.

Special inputs:
- `help` or `?` — show valid bid formats
- `advise` or `a` — show engine recommendation
- `quit` or `q` — exit practice mode
- `hand` or `h` — re-display your hand

#### Error Handling for Practice

- Invalid bid format: "Invalid bid. Try: 1H, 2NT, P, X, XX"
- Illegal bid (e.g., bidding lower than current contract): show the `IllegalBidError` message, re-prompt
- Ctrl+C / Ctrl+D: clean exit

---

## Step 3: Tests

### `tests/cli/test_display.py`

Unit tests for each `format_*` function. Test Rich output by rendering to a string (using `Console(file=StringIO())`).

Key tests:
- `test_format_hand` — known hand produces expected suit lines
- `test_format_hand_eval` — known eval shows correct numbers
- `test_format_auction_from_north` — dealer N, bids start in N column
- `test_format_auction_from_east` — dealer E, first row has empty W/N cells
- `test_format_auction_empty` — no bids yet, shows "?" for current seat
- `test_format_bid_suit` — SuitBid(1, HEARTS) -> "1♥"
- `test_format_bid_pass` — PASS -> "Pass"
- `test_format_bid_double` — DOUBLE -> "X"
- `test_format_contract` — various contract formats
- `test_format_contract_passed_out` — "Passed out"
- `test_format_alternatives_empty` — no alternatives, returns nothing or empty panel
- `test_format_advice` — shows bid and explanation
- `test_format_thought_process` — renders condition results correctly

### `tests/cli/test_app.py`

Integration tests using `typer.testing.CliRunner`.

Key tests:
- `test_advise_opening_hand` — balanced 15 HCP -> recommends 1NT
- `test_advise_with_auction` — "1H P" with spades -> recommends 1S
- `test_advise_bad_hand_format` — shows error
- `test_advise_bad_auction` — shows error
- `test_advise_with_dealer` — `--dealer E` changes seat inference
- `test_advise_with_vulnerability` — `--vulnerability NS`
- `test_practice_quit_immediately` — input "q" exits cleanly
- `test_practice_one_round` — simulate a few bids then quit

For practice tests, use `CliRunner.invoke()` with `input=` to simulate stdin. Keep practice integration tests minimal and focused on "does it start and exit cleanly."

---

## Step 4: Wire Up Exports

Update `src/bridge/cli/__init__.py` to be empty (or minimal) — typer handles the entrypoint via `app:app`.

Update `src/bridge/service/__init__.py` to export updated `BiddingAdvice` (now includes `thought_process`).

---

## Implementation Order

1. **Step 0A-0B**: Condition infrastructure + Rule base class update
2. **Step 0C**: Opening rules migration (~10 rules)
3. **Step 0D**: Response rules migration (~50 rules)
4. **Step 0E**: Rebid rules migration (~65 rules)
5. **Step 0F-0G**: ThoughtProcess on selector + advisor
6. **Step 1**: `display.py` — formatting functions + tests
7. **Step 2**: `app.py` — both commands (`advise` first, then `practice`)
8. **Step 3**: CLI integration tests
9. **Step 4**: Exports, final cleanup

Steps 0C-0E are independent per file. Step 1 can start as soon as Step 0F-0G defines the ThoughtProcess type (even before all rules are migrated). Step 2 depends on Step 1.

---

## Design Decisions

### Auction Grid Column Order

Use **W N E S** — this is the standard layout in bridge diagrams (clockwise from West's perspective). The dealer determines where the first bid appears.

### Bid Display

Always use suit symbols (♠♥♦♣) with color in terminal output:
- ♠ Spades: blue
- ♥ Hearts: red
- ♦ Diamonds: yellow/orange
- ♣ Clubs: green

Pass, X, XX displayed as-is (no color).

### Practice Mode — Record Player's Bid or Engine's?

Record the **player's actual bid**. The auction should reflect what the player chose, even if it differs from the recommendation. This lets the auction continue naturally and the player sees the consequences of their choices.

### Console Object

Display functions return Rich renderables, `app.py` prints them. This keeps display functions pure and testable.

### Rich vs Plain Output

Always use Rich. If someone pipes output to a file, Rich auto-detects and strips formatting. No need for a `--plain` flag.

### OR Rules: Split or Keep?

Keep the 6 OR-logic rules as single classes using `Any(...)`. Splitting into separate rules would duplicate priority management and registration, and for cases like Stayman both paths produce the same bid (2C).

### Thought Process: Conditions vs Templates

The condition system replaces the template-based `thought_process.py` originally planned. Conditions generate thought text directly from evaluation results — no separate generator needed. `src/bridge/service/thought_process.py` is no longer needed.

### Fallback Pass Rules

Rules like `OpenPass` that always apply (`applies() -> True`) don't need conditions. They keep their `applies()` override. The `check()` method returns an empty `CheckResult(passed=True, results=(), computed={})`.

---

## Verification

After Step 0:
- `pdm run check` passes
- All 946+ existing tests pass unchanged
- `BidSelector.think()` on a known hand produces structured trace

After full Phase 1:
- `pdm run check` passes
- `bridge advise --hand "AKQ32.KQ3.J84.A7"` shows 1NT recommendation with thought process
- `bridge advise --hand "AKJ52.KQ3.84.A73" --auction "1H P"` shows 1S response
- `bridge practice` starts, deals a hand, accepts bids, shows advice on request
- `bridge practice --seat S --dealer E` works with different positions
- All display formatting looks correct in terminal
