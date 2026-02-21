# Phase 3: Rule Engine Skeleton

The `engine/` package provides the framework that all bidding rules plug into. No actual SAYC rules yet — this phase builds the machinery: a base rule protocol, a context object that bundles hand evaluation with auction state, a registry that collects rules, and a selector that picks the winning bid.

## Dependencies

Phase 3 builds on:
- `model/` — `Board`, `Hand`, `Bid`, `AuctionState`, `Seat`, `Vulnerability`, `Strain`
- `evaluate/` — `hcp`, `length_points`, `total_points`, `distribution_points`, `controls`, `quick_tricks`, `losing_trick_count`

## Modules

| Module | Purpose |
|--------|---------|
| `engine/context.py` | `BiddingContext` — pre-computed hand metrics + auction queries |
| `engine/rule.py` | `Rule` protocol + `RuleResult` dataclass |
| `engine/registry.py` | `RuleRegistry` — collects and indexes rules by category |
| `engine/selector.py` | `BidSelector` — phase detection + priority-based conflict resolution |
| `engine/__init__.py` | Re-exports public API |

## BiddingContext

A frozen bundle of everything a rule needs to make a decision. Computed once per `advise()` call, passed to every rule.

### Fields

From `Board`:
- `hand: Hand`
- `seat: Seat`
- `auction: AuctionState`
- `vulnerability: Vulnerability`

Pre-computed hand metrics (avoids rules re-computing):
- `hcp: int`
- `length_pts: int`
- `total_pts: int`
- `distribution_pts: int`
- `controls: int`
- `quick_tricks: float`
- `ltc: int`

Derived shape helpers:
- `shape: tuple[int, int, int, int]` — S-H-D-C lengths
- `sorted_shape: tuple[int, ...]` — descending
- `is_balanced: bool`
- `is_semi_balanced: bool`
- `longest_suit: Suit`

Auction convenience (delegate to `AuctionState`):
- `has_opened: bool`
- `opening_bid: tuple[Seat, Bid] | None`
- `partner_last_bid: Bid | None`
- `rho_last_bid: Bid | None`
- `is_competitive: bool`
- `my_bids: list[Bid]` — bids by this seat
- `is_my_first_bid: bool` — this seat has made no non-pass bids
- `is_vulnerable: bool` — whether this seat is vulnerable

### Factory

```python
@classmethod
def from_board(cls, board: Board) -> BiddingContext:
    ...
```

Computes all metrics from the `Board` in one place.

## Rule Protocol

Each rule is a class with a standard interface. Using `typing.Protocol` rather than ABC — keeps rules lightweight, no inheritance required.

```python
class Rule(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def category(self) -> str: ...

    @property
    def priority(self) -> int: ...

    def applies(self, ctx: BiddingContext) -> bool: ...

    def select(self, ctx: BiddingContext) -> RuleResult: ...
```

### Properties

- `name` — unique identifier, dotted convention: `"opening.1nt"`, `"response.major.limit_raise"`
- `category` — which auction phase: `"opening"`, `"response"`, `"rebid_opener"`, `"rebid_responder"`, `"competitive"`, `"convention"`, `"slam"`
- `priority` — higher wins. Bands:
  - 0–99: fallback / catchall rules (e.g., "pass when nothing else applies")
  - 100–199: general rules (e.g., open 1 of a suit)
  - 200–299: specific rules (e.g., open 1NT with 15–17 balanced)
  - 300–399: conventions (e.g., Stayman, Jacoby transfer)
  - 400–499: strong/forcing (e.g., 2C opening)
  - 500+: slam-related

### Methods

- `applies(ctx)` — fast boolean pre-filter. Should be cheap (check HCP range, shape, auction state). Called on every rule in the active category.
- `select(ctx)` — called only if `applies` returned True. Returns a `RuleResult` with the recommended bid and metadata.

## RuleResult

```python
@dataclass(frozen=True)
class RuleResult:
    bid: Bid
    rule_name: str
    explanation: str          # Short machine-generated reason, e.g. "15-17 HCP, balanced"
    alerts: tuple[str, ...]   # Any alerts for opponents (e.g., "Artificial, forcing")
    forcing: bool             # Is this bid forcing on partner?
```

`alerts` uses a tuple (immutable) rather than list. Defaults to empty `()`.
`forcing` defaults to `False`.

## RuleRegistry

Collects all rule instances and indexes them for fast lookup.

```python
class RuleRegistry:
    def register(self, rule: Rule) -> None: ...
    def rules_for(self, category: str) -> list[Rule]: ...
    def all_rules(self) -> list[Rule]: ...
```

- `register()` — adds a rule. Raises on duplicate `name`. **Raises on duplicate priority within the same category** — forces explicit ordering decisions and prevents fragile registration-order dependencies. The bands give 100 slots per tier, so collisions mean you haven't thought about relative ordering.
- `rules_for(category)` — returns rules for a category, sorted by priority descending (highest first)
- `all_rules()` — all registered rules, sorted by priority descending

Rules are registered at import time by the SAYC module (Phase 4+). The registry itself has no knowledge of SAYC — it's system-agnostic.

## BidSelector

The core routing logic. Given a context and a registry, picks the best bid.

```python
class BidSelector:
    def __init__(self, registry: RuleRegistry) -> None: ...
    def select(self, ctx: BiddingContext) -> RuleResult: ...
    def detect_phase(self, ctx: BiddingContext) -> str: ...
    def candidates(self, ctx: BiddingContext) -> list[RuleResult]: ...
```

### Phase Detection

`detect_phase()` determines which rule category to search based on auction state:

| Condition | Category |
|-----------|----------|
| No one has opened (`not has_opened`) | `"opening"` |
| Partner opened, my first non-pass bid, no opponent interference | `"response"` |
| Partner opened, my first non-pass bid, opponent interfered | `"competitive_response"` |
| I opened, partner has responded | `"rebid_opener"` |
| Partner opened, I already responded | `"rebid_responder"` |
| Opponent opened, my first bid | `"competitive"` |

Convention and slam rules are always checked as overlays regardless of phase.

### Selection Logic

`select(ctx)`:
1. Detect the phase
2. Collect all rules for that category from the registry
3. Also collect `"convention"` and `"slam"` rules (overlays)
4. For each rule (highest priority first), call `applies(ctx)`
5. First rule where `applies` returns True: call `select(ctx)` and return the result
6. If no rule applies, return a pass with explanation `"No applicable rule"`

`candidates(ctx)`:
Returns all matching `RuleResult`s (not just the winner). Useful for the LLM layer to explain what was considered.

## Testing Strategy

Phase 3 tests use **mock rules** — tiny rule implementations that always apply or never apply, with known priorities. This validates the framework without any SAYC knowledge.

### Test Classes

| Test Class | What It Validates |
|------------|-------------------|
| `TestBiddingContext` | `from_board()` computes all metrics correctly |
| `TestRuleResult` | Dataclass creation, defaults |
| `TestRuleRegistry` | Registration, duplicate rejection, category lookup, priority ordering |
| `TestPhaseDetection` | Each auction state maps to the correct phase |
| `TestBidSelector` | Priority ordering, overlay merging, fallback to pass |
| `TestCandidates` | Returns all applicable results, not just the winner |

### Mock Rules

```python
class MockRule:
    def __init__(self, name: str, category: str, priority: int, bid: Bid, should_apply: bool = True):
        ...
```

Configurable: set `should_apply=False` to test rules that don't match.

### Phase Detection Scenarios

Test each row of the phase detection table by constructing auction histories:
- Empty auction → `"opening"`
- Partner opened 1H, nothing else → `"response"`
- Partner opened 1H, RHO overcalled 1S → `"competitive_response"`
- I opened 1H, partner responded 2H → `"rebid_opener"`
- Opponent opened 1H → `"competitive"`

## Implementation Order

1. `context.py` — `BiddingContext` with `from_board()` factory
2. `rule.py` — `Rule` protocol + `RuleResult` dataclass
3. `registry.py` — `RuleRegistry`
4. `selector.py` — `BidSelector` with phase detection
5. `__init__.py` — re-exports
6. `tests/engine/test_context.py`
7. `tests/engine/test_registry.py`
8. `tests/engine/test_selector.py`

## Verification

```bash
pdm run test tests/engine/
pdm run check
```

## Open Questions

None — design follows the architecture in PLAN.md.
