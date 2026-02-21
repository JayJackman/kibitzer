# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bridge bidding assistant implementing the SAYC (Standard American Yellow Card) bidding system. Rule-based engine for bid selection with optional Claude API integration for natural-language explanations and alternative bid analysis.

## Tech Stack

- Python 3.12, PDM package manager, `src/` layout
- Ruff (lint + format), mypy (strict), pytest + hypothesis

## Common Commands

```bash
pdm install              # Install all dependencies
pdm run test             # Run tests
pdm run test-cov         # Run tests with coverage
pdm run lint             # Ruff linter
pdm run format           # Ruff formatter
pdm run typecheck        # mypy strict
pdm run check            # All three: lint + typecheck + test
```

Run a single test file or pattern:
```bash
pdm run pytest tests/model/test_card.py
pdm run pytest tests/ -k "test_opening"
```

## Architecture

```
cli --> service/advisor --> engine (rule-based, deterministic)
                       --> llm    (Claude API, optional)
                       --> evaluate (hand metrics)
                       --> model  (pure domain objects)
```

Each layer only depends downward. The `service/advisor.py` is the stable API surface.

## Code Conventions

- **Never use string-quoted type annotations** like `-> "Foo"`. When forward references are needed, add `from __future__ import annotations` to the file. Only include the import when it's actually necessary (e.g., forward references, self-referencing types).
- All tool config lives in `pyproject.toml` — no separate config files.
- Pre-commit hooks run ruff + mypy on every commit.
