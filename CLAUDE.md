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

## Rule Directory Structure

Rules live under `src/bridge/engine/rules/sayc/`. Each directory maps to one auction round:

```
opening/       # Round 1: opener's first bid
response/      # Round 2: responder's first bid
rebid/         # Round 3: opener's second bid
reresponse/    # Round 4: responder's second bid (future)
further/       # Round 5+: later bids (future)
```

Within each directory, files are organized by opening type: `suit.py` (after 1-of-a-suit), `nt.py` (after NT opening), `strong.py` (after 2C), `preempt.py` (after weak/preemptive opening). Not every directory needs all file types — only create what's needed.

Competitive bidding (overcalls, doubles) cuts across all rounds and will be handled separately.

## SAYC Rule Accuracy

Every bidding rule must be accurate to the official SAYC (Standard American Yellow Card) system as published by the ACBL. The primary reference is the ACBL SAYC System Booklet (SP-3, revised January 2006).

- **Use extended thinking for all bridge theory work.** When implementing rules, adjusting rules, setting forcing status, giving bidding advice, or answering any bridge theory question, use deep/extended thinking to reason carefully and verify accuracy before responding. Bridge bidding has many subtle edge cases (e.g., 2/1 is forcing one round in SAYC, NOT game forcing) — think it through.
- **Before implementing any rule**, verify the HCP ranges, suit length requirements, shape constraints, and forcing status against the SAYC booklet and the research documents in `research/`.
- **Do not invent or assume rules.** If the SAYC booklet is silent on a specific situation, note the gap rather than guessing. Common teaching aids (e.g., "open the suit below the singleton" for 4-4-4-1) should be marked as common practice, not official SAYC.
- **Each rule's `explanation` field and test assertions must cite the specific SAYC guideline** (e.g., "15-17 HCP, balanced — SAYC 1NT opening").
- **Conventions not in SAYC must not be implemented** unless explicitly noted as extensions. The following are NOT part of standard SAYC: Gambling 3NT, Roman Key Card Blackwood, New Minor Forcing, Drury, Lebensohl, Inverted Minors, Bergen Raises, Splinter Bids.
- When in doubt, consult: `research/00-overview.md` (system summary), `research/01-opening-bids.md` through `research/06-slam.md` (detailed rules).

## Refactoring Policy

- **Prefer clean refactors over compatibility shims.** When restructuring code (moving types to a new file, renaming exports, splitting modules), update all consumers rather than adding re-exports, aliases, or backwards-compatibility wrappers. A few extra file edits are worth it for a clean result.
- **If a refactor touches many files**, present the options to the user and let them decide whether to proceed. Don't silently take the shortcut — explain the tradeoff (e.g., "we can add a re-export to avoid touching 12 files, or update all 12 for a cleaner result").

## Code Conventions

- **Never use string-quoted type annotations** like `-> "Foo"`. When forward references are needed, add `from __future__ import annotations` to the file. Only include the import when it's actually necessary (e.g., forward references, self-referencing types).
- **Inline single-use variables** when the expression is legible on its own. Don't extract a local variable just to name something used once.
- **Use plain ASCII in source code.** Hyphens (`-`) not en dashes, `<=` not `≤`, etc.
- All tool config lives in `pyproject.toml` — no separate config files.
- Pre-commit hooks run ruff + mypy on every commit.
- When writing anything related to the web-app (i.e., in the frontend folder) err on more verbose comments. I am new to web-app code and would appreciate helpful comments that help me understand both *why* and *what* is happening in the code.

## Frontend Patterns (React Router v7)

The frontend uses React Router v7's **data router** patterns (`createBrowserRouter` + `RouterProvider`). Follow these conventions:

- **Loaders for data fetching.** Use route `loader` functions to fetch data before a page renders. Don't use `useEffect` + `useState` for initial data loading -- loaders run before the component mounts, avoiding loading spinners and flash of wrong content.
- **Actions for mutations.** Use route `action` functions to handle form submissions (login, register, creating tables, etc.). Pair with React Router's `<Form>` component, `useActionData()` for error display, and `useNavigation()` for submission state.
- **Uncontrolled form inputs.** Use `name` attributes on inputs instead of controlled state (`value` + `onChange`). The action reads values via native `FormData`.
- **Auth via loader, not context.** Authentication is checked by the `protectedLoader` in `App.tsx`. Protected routes get user data from `useRouteLoaderData("protected")`. There is no AuthProvider or auth context.
- **`useFetcher` for non-navigation mutations.** For actions that shouldn't cause a page navigation (e.g., logout button in the nav bar), use `useFetcher()` and `fetcher.Form`.
