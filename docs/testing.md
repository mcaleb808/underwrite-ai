# How we test

Tests are organised in layers, each one designed to catch a different class of mistake. The fast layers run on every pull request; anything that touches a real LLM is opt-in.

The short version: **fast, deterministic tests on every PR; slow LLM-backed tests on demand; a separate evaluation suite that asks "did the AI make a defensible decision".**

---

## What runs in CI on every PR

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs three things, in parallel where possible, on every pull request:

- **Backend**: `ruff check`, `ruff format --check`, `pytest -m "not slow"` — no LLM credentials needed, no network.
- **Frontend**: `tsc --noEmit`, `eslint --max-warnings=0`, `next build`.
- **Markdown lint** (added quietly via pre-commit hooks).

If any of these fail, the PR can't be merged. Nothing fancy.

---

## The test layers

| Layer | Where | What it catches |
|---|---|---|
| **Tools (math)** | [`tests/test_tools.py`](../apps/api/tests/test_tools.py), `test_cost.py` | risk-scoring math, BMI / age-band helpers, district-prevalence lookup, cost estimator |
| **Routes** | [`tests/test_applications_route.py`](../apps/api/tests/test_applications_route.py), `test_review_routes.py`, `test_delete_cancel_routes.py`, `test_list_and_files_routes.py`, `test_personas_route.py`, `test_districts_route.py` | request validation, response shape, status codes, decision-lifecycle gates, cancel + orphan-cancel branches |
| **RAG units** | [`tests/test_chunks.py`](../apps/api/tests/test_chunks.py), `test_ingest.py` | the markdown chunker output, ingest idempotency |
| **RAG end-to-end** *(slow)* | [`tests/test_rag.py`](../apps/api/tests/test_rag.py) | retrieval drift on a fixed set of known queries against the real embedding model |
| **Event bus + SSE** | [`tests/test_events_sse.py`](../apps/api/tests/test_events_sse.py), `test_events_schema.py` | pub/sub semantics, SSE history replay, typed-event payload validation |
| **Node resilience** | [`tests/test_node_resilience.py`](../apps/api/tests/test_node_resilience.py) | LLM retry behaviour, error events on exhaustion, that node failures don't crash the run |
| **Email** | [`tests/test_email_providers.py`](../apps/api/tests/test_email_providers.py), `test_email_composer.py` | provider Protocol + fake double, composer prompt + template fallback |
| **Observability** | [`tests/test_log.py`](../apps/api/tests/test_log.py), `test_health.py` | log binding via context vars, `/health` and `/metrics` responses |
| **Eval scoring** | [`tests/test_eval_scoring.py`](../apps/api/tests/test_eval_scoring.py) | the eval runner's check logic itself (so the eval doesn't lie to us) |
| **Smoke (manual)** | [`apps/api/src/scripts/smoke_test.py`](../apps/api/src/scripts/smoke_test.py) | full graph end-to-end against a stubbed LLM |

---

## Why some tests are marked "slow"

Slow tests need real OpenAI / OpenRouter credentials and hit the live model APIs. They cost money, they introduce flakiness, and they're slow — so they're excluded from CI by default. To run them locally:

```bash
cd apps/api && uv run pytest -m slow
```

The `slow` marker is the seam: anything that needs a real LLM goes behind it; everything else stays in the fast suite.

---

## Beyond unit tests

Two complementary surfaces handle what unit tests can't:

- **The golden-case eval suite** — five representative applicants run through the real graph end-to-end, with verdicts, bands, loadings, and citations checked against bounds. This is what answers "did the AI do the right thing?" See [`docs/evaluation.md`](evaluation.md).
- **The live event timeline** — every run persists a typed event for each agent, surfaced in the dashboard. Useful for spot-checking decisions that didn't trip an automated assertion but feel off. The reviewer can read the exact reasoning the model produced and the rules it cited.
