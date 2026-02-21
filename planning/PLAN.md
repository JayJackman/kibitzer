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
│   │   └── rules/      # One module per rule category
│   │       ├── opening.py, opening_nt.py, opening_strong.py, opening_preempt.py
│   │       ├── response_major.py, response_minor.py, response_nt.py
│   │       ├── response_2c.py, response_weak.py
│   │       ├── rebid_opener.py, rebid_responder.py
│   │       ├── competitive.py, negative_double.py
│   │       ├── conventions.py  (Stayman, Jacoby transfers, etc.)
│   │       ├── slam.py         (Blackwood, Gerber, cue bids)
│   │       └── passed_hand.py
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

| Condition | Category |
|-----------|----------|
| No non-pass bids yet | `opening` |
| Partner opened, my first bid, no interference | `response` |
| Partner opened, my first bid, opponent interfered | `competitive_response` |
| I opened, partner responded | `rebid_opener` |
| Partner opened, I responded | `rebid_responder` |
| Opponent opened, my first bid | `competitive` |
| `convention` and `slam` | Always checked as overlays |

## LLM Integration

Two optional Claude API calls, controlled by CLI flags:

1. **Explain** (`--explain`): Given the hand, auction, selected bid, and all candidate rules, generate a natural-language explanation with key factors.

2. **Alternatives** (`--alternatives`): Ask Claude to suggest unconventional-but-viable bids, each with a weight (0.0-1.0 confidence), rationale, and risk assessment. Uses Pydantic structured output.

Both are skipped with `--no-llm` for offline/fast usage.

## Build Order (10 phases)

### Phase 1: Domain Model
`model/` package (Card, Hand, Bid, AuctionState, Seat, Vulnerability). Foundation for everything.

### Phase 2: Hand Evaluation
`evaluate/` package (HCP, distribution points, quick tricks, LTC, controls).

### Phase 3: Rule Engine Skeleton
`rule.py`, `registry.py`, `selector.py`, `context.py`. Test with mock rules.

### Phase 4: Opening Bid Rules
Simplest category (no prior auction context). Validates the architecture.

### Phase 5: Response Rules
Adds auction-context dependency. Forces phase-detection to work.

### Phase 6: Rebid + Competitive Rules
Largest state space. Build incrementally.

### Phase 7: Convention + Slam Rules
Overlay rules (Stayman, Blackwood, etc.).

### Phase 8: CLI
Wire up typer, input parsing, rich output formatting.

### Phase 9: LLM Integration
Claude API client, prompts, structured output parsing.

### Phase 10: Regression Baseline
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
