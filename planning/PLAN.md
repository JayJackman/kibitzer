# Bridge Bidding Assistant — Implementation Plan

## Context

Build a bridge bidding assistant that takes a hand (and auction history) as input, recommends the best SAYC bid with explanations, and optionally suggests alternative bids with confidence weights. The system uses deterministic rules for correctness and Claude API for natural-language explanations and creative alternative analysis.

## Tech Stack

- **Python 3.12**, `src/` layout package, **PDM** package manager
- **typer + rich** for CLI
- **pydantic** for structured LLM output
- **anthropic** SDK for Claude API
- **pytest + hypothesis + PyYAML** for testing

## Architecture

```
cli --> service/advisor --> engine (rule-based, deterministic)
                       --> llm    (Claude API, optional)
                       --> evaluate (hand metrics)
                       --> model  (pure domain objects)
```

Each layer only depends downward. The `service/advisor.py` is the stable API surface — CLI, future web/mobile all call `BiddingAdvisor.advise()`.

## Project Structure

```
bridge/
├── pyproject.toml
├── src/bridge/
│   ├── model/          # Card, Hand, Bid, AuctionState, Seat, Vulnerability
│   ├── evaluate/       # HCP, distribution points, quick tricks, LTC, controls
│   ├── engine/         # Rule engine
│   │   ├── rule.py     # Base Rule class + RuleResult dataclass
│   │   ├── registry.py # Collects rules, indexes by category
│   │   ├── selector.py # Phase detection + priority-based conflict resolution
│   │   ├── context.py  # BiddingContext (hand eval + auction state bundle)
│   │   ├── sayc.py     # Wires all SAYC rules into one system
│   │   └── rules/sayc/  # SAYC bidding system rules
│   │       ├── opening/     # Round 1: opener's first bid
│   │       │   ├── suit.py, nt.py, strong.py, preempt.py
│   │       ├── response/    # Round 2: responder's first bid
│   │       │   ├── suit.py
│   │       ├── rebid/       # Round 3: opener's second bid
│   │       │   ├── suit.py  (after 1-of-a-suit opening)
│   │       │   ├── nt.py    (after NT opening — Stayman/transfers; future)
│   │       ├── reresponse/  # Round 4: responder's second bid (future)
│   │       ├── further/     # Round 5+: later bids (future)
│   │       └── competitive/ # Overcalls, doubles (future, cross-cutting)
│   ├── llm/            # Claude API integration
│   │   ├── client.py   # Thin Anthropic SDK wrapper
│   │   ├── prompts.py  # System/user prompt templates
│   │   ├── schemas.py  # Pydantic models (BidExplanation, AlternativeBid)
│   │   └── analyzer.py # Orchestrates explain + alternative-analysis calls
│   ├── service/
│   │   └── advisor.py  # BiddingAdvisor: composes engine + LLM
│   └── cli/
│       ├── app.py      # typer commands (bid, evaluate, interactive)
│       ├── parser.py   # Parse hand/auction strings
│       └── formatter.py# Pretty-print with rich
└── tests/
    ├── conftest.py
    ├── model/, evaluate/, engine/, llm/, cli/
    └── engine/scenarios/  # YAML files with known hand → bid mappings
```

## Key Design: Prioritized Rule Objects

Each SAYC rule is a self-contained class with:
- `name` — unique identifier (e.g., `"opening.1nt"`)
- `category` — which auction phase it belongs to (`"opening"`, `"response"`, `"rebid_opener"`, etc.)
- `priority` — higher number wins when multiple rules match (0-99 fallback, 100-199 general, 200-299 specific, 300-399 conventions, 400-499 strong/forcing, 500+ slam)
- `applies(ctx)` — fast boolean pre-filter
- `select(ctx)` — returns a `RuleResult` with the bid, explanation, and metadata

The `BidSelector` routes by auction phase, then picks the highest-priority matching rule. Convention and slam rules are always checked as overlays.

## Phase Detection Logic

The selector determines which rule category to search based on auction state:

| Condition | Category | Directory |
|-----------|----------|-----------|
| No non-pass bids yet | `opening` | `opening/` |
| Partner opened, my first bid, no interference | `response` | `response/` |
| Partner opened, my first bid, opponent interfered | `competitive_response` | `competitive/` |
| I opened, partner responded | `rebid_opener` | `rebid/` |
| Partner opened, I responded, opener rebid | `reresponse` | `reresponse/` |
| Round 5+ | `further` | `further/` |
| Opponent opened, my first bid | `competitive` | `competitive/` |
| `convention` and `slam` | Always checked as overlays | (cross-cutting) |

Each directory under `rules/sayc/` maps to one auction round. Within each directory, files are organized by opening type (e.g., `suit.py`, `nt.py`) following the same pattern as `opening/`.

## LLM Integration

Two optional Claude API calls, controlled by CLI flags:

1. **Explain** (`--explain`): Given the hand, auction, selected bid, and all candidate rules, generate a natural-language explanation with key factors.

2. **Alternatives** (`--alternatives`): Ask Claude to suggest unconventional-but-viable bids, each with a weight (0.0-1.0 confidence), rationale, and risk assessment. Uses Pydantic structured output.

Both are skipped with `--no-llm` for offline/fast usage.

## Build Order

### Phase 1: Domain Model ✅
`model/` package (Card, Hand, Bid, AuctionState, Seat, Vulnerability). Foundation for everything.

### Phase 2: Hand Evaluation ✅
`evaluate/` package (HCP, distribution points, quick tricks, LTC, controls, Bergen points).

### Phase 3: Rule Engine Skeleton ✅
`rule.py`, `registry.py`, `selector.py`, `context.py`. Test with mock rules.

### Phase 4: Opening Bid Rules ✅
All 9 opening rules (1-suit, NT, 2C, weak twos, preempts, pass). Complete.

### Phase 5: Response Rules ✅
All 15 response rules to 1-of-a-suit openings (+ pass). Complete.

### Phase 6: Opener's Rebids (partial) ✅
30 rebid rules covering 5 response types (single raise, limit raise, 1NT, new suit 1-level, 2-over-1). In `rebid/suit.py`.

### Phase 7: Complete 1-of-a-suit Pipeline
Fill remaining rebid gaps (17 new rules): Jacoby 2NT rebids, jump shift rebids, 2NT-over-minor rebids, help suit game tries, double-jump bids, pass after game-level responses. See `planning/phase7-complete-suit-pipeline.md`.

### Phase 8: Complete All Responses + Rebids
Add responses to every other opening type (1NT, 2NT, 2C, weak twos, preempts) and their corresponding opener rebids. ~75 new rules. See `planning/phase7-complete-suit-pipeline.md` Phase B section.

### Phase 9: Responder's Rebids + Further Bidding
Rules in `reresponse/` and `further/`. Includes handling game tries from responder's side.

### Phase 10: Competitive Bidding
Overcalls, doubles, negative doubles. Cross-cutting across all rounds.

### Phase 11: CLI
Wire up typer, input parsing, rich output formatting.

### Phase 12: LLM Integration
Claude API client, prompts, structured output parsing.

### Phase 13: Regression Baseline
Run engine against hundreds of test hands, freeze as baseline.

## Testing Strategy

- **Unit tests**: Each rule class tested in isolation with known hands
- **Scenario-driven integration tests**: YAML files mapping hand + auction -> expected bid, parametrized with pytest
- **Property-based tests** (hypothesis): Random valid hands always produce a legal bid
- **LLM tests**: Mock Claude client, verify prompt formatting and response parsing
- **Regression baseline**: `pytest --baseline` compares current output against frozen known-good results

## Future Extensibility

- New bidding systems (2/1, Acol) implement the same `BiddingSystem` protocol and register their own rules -- many rules (opening bids, Blackwood) can be reused
- Web/mobile frontends call `BiddingAdvisor.advise()` via a REST API layer (FastAPI)
- `BiddingAdvice` dataclass serializes to JSON for API responses

## Verification

After each phase:
```bash
pytest tests/                    # Run all tests
pytest tests/engine/ -k "opening" # Run single category
bridge bid "AKJ52.KQ3.84.A73"   # Smoke test CLI
bridge bid "AKJ52.KQ3.84.A73" --alternatives  # Test LLM integration
```
