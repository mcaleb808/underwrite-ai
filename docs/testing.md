# Test strategy

Tests are layered so each catches a different class of regression. The fast suite (no LLM calls, no network) runs on every PR via [`.github/workflows/ci.yml`](../.github/workflows/ci.yml); slow tests are gated behind `pytest.mark.slow` and run on demand.

## What each layer catches

| Layer | Where | What it catches |
|---|---|---|
| Tools | [`tests/test_tools.py`](../apps/api/tests/test_tools.py), `test_cost.py` | risk-scoring math, BMI / age-band helpers, district-prevalence lookup, cost estimator |
| Routes | [`tests/test_applications_route.py`](../apps/api/tests/test_applications_route.py), `test_review_routes.py`, `test_delete_cancel_routes.py`, `test_list_and_files_routes.py`, `test_personas_route.py`, `test_districts_route.py` | request validation, response serialization, status codes, decision lifecycle gates, cancel + orphan-cancel branches |
| RAG units | [`tests/test_chunks.py`](../apps/api/tests/test_chunks.py), `test_ingest.py` | markdown chunker output, ingest idempotency |
| RAG end-to-end *(slow)* | [`tests/test_rag.py`](../apps/api/tests/test_rag.py) | retrieval drift on a fixed set of known queries against the real embedding model |
| Event bus + SSE | [`tests/test_events_sse.py`](../apps/api/tests/test_events_sse.py), `test_events_schema.py` | pub/sub semantics, SSE history replay, typed-event payload validation |
| Node resilience | [`tests/test_node_resilience.py`](../apps/api/tests/test_node_resilience.py) | LLM retry behaviour, error events on exhaustion, that node failures don't crash the run |
| Email | [`tests/test_email_providers.py`](../apps/api/tests/test_email_providers.py), `test_email_composer.py` | provider Protocol + fake double, composer prompt + template fallback |
| Observability | [`tests/test_log.py`](../apps/api/tests/test_log.py), `test_health.py` | log binding via contextvars, /health and /metrics responses |
| Eval scoring | [`tests/test_eval_scoring.py`](../apps/api/tests/test_eval_scoring.py) | unit tests for the eval runner's check logic |
| Smoke | [`apps/api/src/scripts/smoke_test.py`](../apps/api/src/scripts/smoke_test.py) | full graph end-to-end against a stub LLM (manual) |

## CI vs slow

CI runs `pytest -m "not slow"` on every PR — no LLM credentials needed, no network, deterministic. The frontend gate is `tsc --noEmit` + `eslint --max-warnings=0` + `next build`.

Slow tests need real OpenAI/OpenRouter credentials; they exercise embeddings, retrieval, and the full LangChain stack against the live API. Run them locally:

```bash
cd apps/api && uv run pytest -m slow
```

## Beyond unit tests

Two complementary surfaces:

- **Golden-case eval suite** — see [`docs/evaluation.md`](evaluation.md). Five representative applicants, run end-to-end through the real graph, asserted against verdict bounds, citation requirements, and bias guards. This is the closest thing to "did the agent do the right thing".
- **Live event timeline** — every run persists a typed event for each node, surfaced in the dashboard. Useful for spot-checking decisions that didn't trip an automated assertion but feel off — the reviewer can read the exact reasoning the model produced and the rules it cited.
