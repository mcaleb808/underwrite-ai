# Observability

Three layers, each independently useful: structured logs at the request level, LLM tracing of the agent graph, and operational health/metrics endpoints for liveness probes and at-a-glance counters.

## Structured logging

[`apps/api/src/services/log.py`](../apps/api/src/services/log.py) configures `structlog` with `contextvars.merge_contextvars` so any field bound at the request boundary appears on every downstream log line. Output is JSON; stdlib loggers (uvicorn, sqlalchemy) are routed through the same renderer.

Request-ID propagation sits in [`apps/api/src/middleware/request_id.py`](../apps/api/src/middleware/request_id.py). Every request is stamped with `X-Request-ID` (echoed in the response header) and bound to the structlog context for the duration of the request — so a single log query by `request_id` returns the full trail across the route, the orchestrator, and every node it ran.

Each LLM call also emits an `llm_call` log entry with `model`, `latency_ms`, prompt/completion/total tokens, and (via [`services/cost.py`](../apps/api/src/services/cost.py)) an estimated USD cost. The same data feeds the `/metrics` counters.

## LLM tracing

[`apps/api/src/services/tracing.py`](../apps/api/src/services/tracing.py) wires up OpenTelemetry once on startup:

- a `TracerProvider` for the `underwrite-api` service;
- when `K_SERVICE` is set (Cloud Run), a `BatchSpanProcessor` exporting to GCP Cloud Trace via `opentelemetry-exporter-gcp-trace`;
- when `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are set, the Langfuse SDK shares the same `TracerProvider` so LangChain callback spans land in Langfuse Cloud as one nested trace tree;
- FastAPI auto-instrumentation when an `app` is provided.

Langfuse callbacks are attached at the **graph** level (not per-LLM) in [`services/log.py`](../apps/api/src/services/log.py) `graph_callbacks()` and threaded into the graph via `config["callbacks"]` in the orchestrator. That single placement is what makes each underwriting run nest as one trace with five child node spans, each with its LLM children, tokens, and cost.

The orchestrator also opens a manual `underwriting.run` span around each task with `langfuse.session.id`, `langfuse.user.id`, `underwriting.task_id`, and (on completion) verdict / risk_band / risk_score / revision_count attributes — see [`services/orchestrator.py`](../apps/api/src/services/orchestrator.py). The eval runner does the same with `underwriting.eval=true` so eval traces are filterable in Langfuse.

**Honest caveat.** On Cloud Run, LangChain callback spans fired inside FastAPI's `BackgroundTask` context are silenced before any OTel processor sees them — a known interaction between LangChain's callback context propagation and the OTel + Background-task combination. Synchronous spans on the same provider export fine. Local development against Langfuse Cloud shows the full nested timeline; the deployed environment is silent for callback spans. The local trace is the source of truth for the agent timeline today.

## Health and metrics

Both endpoints live in [`apps/api/src/routes/health.py`](../apps/api/src/routes/health.py).

**`GET /api/v1/health`** — liveness probe. Reports `status` (`ok` / `degraded`) plus per-dependency state for the DB (`SELECT 1`), Chroma (`count() > 0`), and the LLM provider (`OPENROUTER_API_KEY` configured).

```json
{
  "status": "ok",
  "db": "ok",
  "chroma": "ok",
  "llm_provider": "configured"
}
```

**`GET /api/v1/metrics`** — at-a-glance counters since the last process restart.

```json
{
  "decisions_total": 42,
  "decisions_failed": 1,
  "tasks_total": 47,
  "total_tokens_since_start": 184321,
  "total_cost_usd_since_start": 0.213,
  "llm_calls_since_start": 156
}
```

Token + cost counters are sourced from the in-memory `LLMObservability` callback in [`services/log.py`](../apps/api/src/services/log.py) — the same callback that tags every node's LLM call with `model`, `latency_ms`, and `total_tokens`. The same numbers drive the token/cost pill in the dashboard.

## Live event stream

A separate observability surface aimed at the human in the loop, not at oncall: every node emits a typed event (`DocParserParsed`, `DecisionDrafted`, `CriticReviewed`, ...) that the orchestrator persists to SQLite *and* publishes to an in-process pub/sub bus ([`services/event_bus.py`](../apps/api/src/services/event_bus.py)). The browser consumes both — DB replay first, then live tail via SSE — so a reviewer joining mid-run still sees every step. See [`docs/architecture.md`](architecture.md) for the sequence diagram.
