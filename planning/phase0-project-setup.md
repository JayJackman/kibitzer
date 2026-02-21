# Phase 0: Project Setup & Environment

Set up a production-grade Python project structure using PDM as the package manager.

## Package Manager

**PDM** — PEP 621 compliant, uses `pyproject.toml` as the single source of truth, supports lockfiles, and manages virtual environments.

## Project Layout

```
bridge/
├── pyproject.toml          # All project metadata, dependencies, tool config
├── pdm.lock                # Locked dependency versions
├── .python-version         # Pin Python version
├── .gitignore
├── .env.example            # ANTHROPIC_API_KEY placeholder
├── README.md
├── CLAUDE.md               # Claude Code guidance
├── planning/               # Phase plans (this folder)
├── src/
│   └── bridge/
│       ├── __init__.py
│       ├── py.typed        # PEP 561 marker for type checking
│       ├── model/
│       ├── evaluate/
│       ├── engine/
│       ├── llm/
│       ├── service/
│       └── cli/
└── tests/
    ├── conftest.py
    ├── model/
    ├── evaluate/
    ├── engine/
    ├── llm/
    └── cli/
```

Uses `src/` layout (PEP 517) — prevents accidental imports of the package from the project root.

## Python Version

3.12 (latest stable, good performance, improved error messages, typing improvements).

## Dependencies

### Runtime
| Package | Purpose |
|---------|---------|
| `typer` | CLI framework |
| `rich` | Terminal formatting (tables, colors, panels) |
| `pydantic` | Structured LLM output, data validation |
| `anthropic` | Claude API SDK |

### Development
| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `hypothesis` | Property-based testing |
| `pyyaml` | Test scenario files |
| `ruff` | Linting + formatting (replaces flake8, isort, black) |
| `mypy` | Static type checking |
| `pre-commit` | Git hooks for lint/format/type checks |

## Tool Configuration

All tool config lives in `pyproject.toml` — no separate `.flake8`, `mypy.ini`, etc.

### Ruff
- Line length: 88 (black default)
- Target: Python 3.12
- Rules: E, F, W, I (isort), UP (pyupgrade), B (bugbear), SIM (simplify)
- Format: black-compatible

### Mypy
- Strict mode
- Disallow untyped defs
- No implicit optional

### Pytest
- Test paths: `tests/`
- Coverage target: `src/bridge`
- Strict markers

## Entry Point

```toml
[project.scripts]
bridge = "bridge.cli.app:app"
```

Installed via `pdm install`, then `bridge bid "AKJ52.KQ3.84.A73"` works.

## Git Setup

- Initialize repo
- `.gitignore` for Python (venv, __pycache__, .mypy_cache, .ruff_cache, dist/, etc.)
- Initial commit with project skeleton

## CI/CD (future)

Not setting up now, but the structure supports GitHub Actions with:
```
pdm install --dev
pdm run lint
pdm run typecheck
pdm run test
```

## PDM Scripts

```toml
[tool.pdm.scripts]
test = "pytest tests/"
test-cov = "pytest tests/ --cov=src/bridge --cov-report=term-missing"
lint = "ruff check src/ tests/"
format = "ruff format src/ tests/"
typecheck = "mypy src/"
check = { composite = ["lint", "typecheck", "test"] }
```

## Resolved Decisions

1. **Package manager**: PDM
2. **Layout**: `src/` layout
3. **Linter/formatter**: Ruff (single tool replaces black + flake8 + isort)
4. **Type checker**: mypy in strict mode

## Resolved from Discussion

5. **Pre-commit hooks**: Yes, from day one. Ruff lint/format + mypy on every commit.
6. **Python version**: 3.12
7. **Makefile**: No. PDM scripts only (`pdm run test`, `pdm run lint`, etc.).

8. **Coverage threshold**: No hard gate. Report coverage but don't fail the build on a percentage. YAML scenario tests are more meaningful than a coverage number.

## Open Questions

None — Phase 0 design is resolved.
