# Working in this repo

Quick orientation for AI coding assistants. Start with the
[`README.md`](README.md) for what this project is and
[`docs/architecture.md`](docs/architecture.md) for how it's wired.

## Layout

- `apps/api/` — FastAPI + LangGraph backend (Python 3.12, `uv`)
- `apps/web/` — Next.js 16 dashboard (TypeScript, App Router, Tailwind 4)
- `apps/api/src/graph/` — graph state, builder, routing, and the 5 nodes
- `apps/api/src/services/` — orchestrator, event bus, email providers
- `apps/api/src/tools/` — pure deterministic helpers (BMI, scoring, etc.)
- `apps/api/tests/` — CI-safe by default; LLM-touching tests are
  `@pytest.mark.slow` and excluded from `make test`

## Conventions

- **Commits:** concise, lowercase after the type/scope, no Claude attribution
  anywhere (no `Co-Authored-By: Claude`, no AI-tool footers).
  Examples: `feat(graph): pin foundational rules in rag`,
  `test(api): cover sse history replay`.
- **Branches:** describe the content, no day numbers.
  Good: `feat/dashboard-polish`. Bad: `feat/day-9`.
- **PRs:** open one per logical unit; never push to `main` directly.
  Keep PR descriptions to a few short bullets — the diff tells the rest.
- **Code:** module docstrings explain role; inline comments only where the
  *why* is non-obvious. No commented-out code, no premature abstractions.

## Workflow

```bash
make test    # ruff-clean + 56 tests pass before committing
make lint    # api ruff + web eslint
make demo    # full pipeline against all 5 seed personas (real LLM, ~$0.05)
```

Pre-commit hooks (ruff + ruff-format) run on every commit.

## Things to know

- LLMs are reached via OpenRouter. The strong model is
  `anthropic/claude-sonnet-4.5`; the fast model is `openai/gpt-4o-mini`.
  Embeddings use OpenAI directly (`text-embedding-3-small`).
- The Rwanda region adapter (`adapters/rw.py`) provides a deterministic
  regex bias check that's merged with the LLM critic — the regex is the
  floor and cannot be overridden.
- The orchestrator persists each event as it streams; the SSE route replays
  history first, then attaches to the in-process event bus for live updates.
- Seed PDFs at `apps/api/src/data/medical_pdfs/*.pdf` are gitignored
  generated artifacts — `tests/conftest.py` writes stubs if they're missing
  so CI doesn't depend on local state.
