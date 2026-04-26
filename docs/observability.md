# Observability

When something goes wrong in production, you need three things: **logs to read, traces to follow, and counters to glance at**. This page explains how each one is set up and what you'd look at when.

In one line: every request gets a unique ID that follows it through every log line and every AI call, the AI calls themselves are recorded as nested traces in Langfuse, and there are two endpoints (`/health` and `/metrics`) to check whether everything is alive and what it has been doing.

---

## Logs you can actually grep

Logs are emitted as JSON, one event per line. That sounds bureaucratic but it's the right shape: you can pipe them into any log viewer, filter by field, and the structure stays intact. The setup lives in [`services/log.py`](../apps/api/src/services/log.py).

The most useful trick: **every request is given an `X-Request-ID` header on the way in, and that ID is bound to the log context**. So every log line emitted while handling that request — the route, the orchestrator, every agent in the graph — automatically carries the same `request_id`. To debug a complaint like "this case looks wrong", grab the request ID from the response header and search for it; you get the entire timeline for that one user.

📁 [`apps/api/src/middleware/request_id.py`](../apps/api/src/middleware/request_id.py)

Each LLM call also emits its own log line with the model name, latency in ms, prompt/completion/total tokens, and an estimated USD cost. That's the same data feeding the token+cost pill you see in the dashboard, and the same data behind `/metrics`.

---

## Traces — what the AI did, in order

For the AI side, Langfuse Cloud is the trace backend. Each underwriting run shows up as **one trace tree** with nested children for each agent and each LLM call within that agent. You see the prompts, the responses, the tokens, the latency, and (with Langfuse's pricing data) a cost estimate per call.

The setup ([`services/tracing.py`](../apps/api/src/services/tracing.py)) is small:

- spin up an OpenTelemetry `TracerProvider`;
- if `K_SERVICE` is set (i.e. we're on Cloud Run), also export to GCP Cloud Trace;
- if Langfuse keys are set, the Langfuse SDK shares the same tracer so its callback spans land in Langfuse Cloud as one tree;
- auto-instrument FastAPI so every HTTP request gets its own span.

The trick that makes it nest cleanly is attaching the Langfuse callback at the **graph** level, not per-LLM. That single placement is what makes "five agents, with their LLM children, in one tree" possible.

> **Honest caveat.** This works beautifully *locally*. On Cloud Run, AI-call spans fired inside FastAPI's `BackgroundTasks` context are silenced before any exporter sees them — a known interaction between LangChain's callback context and the OTel SDK in that specific runtime combination. Synchronous spans on the same provider export fine. Local Langfuse traces remain the source of truth for the agent timeline today.

---

## `/health` and `/metrics`

Two endpoints, both in [`routes/health.py`](../apps/api/src/routes/health.py).

### `GET /api/v1/health`

Quick liveness check — meant for an uptime monitor or a Cloud Run probe. Returns one of `ok` or `degraded` overall, plus the state of each dependency:

```json
{
  "status": "ok",
  "db":     "ok",
  "chroma": "ok",
  "llm_provider": "configured"
}
```

If the DB is unreachable, Chroma is empty, or the LLM API key is missing, you'll see `degraded`.

### `GET /api/v1/metrics`

A small, human-readable dashboard of "what has this process been doing since it started":

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

The token + cost numbers come from the same in-memory counter that records every LLM call. Restart the process and these reset to zero — they're for at-a-glance sanity, not long-term billing.

---

## Live event stream (the human-facing observability)

Separate from the production-ops surface above, there's a live event stream aimed at the underwriter watching a case run. Every agent emits a typed event the moment it finishes a step — `DocParserParsed`, `DecisionDrafted`, `CriticReviewed`, etc. — and those events land in two places at once:

- **persisted to SQLite**, so they survive a restart and the timeline is always replayable;
- **published to an in-process pub/sub bus** ([`services/event_bus.py`](../apps/api/src/services/event_bus.py)), which the dashboard subscribes to via Server-Sent Events.

When you open a case mid-run in the dashboard, the route first replays history from SQLite (so you don't miss anything that already happened), then attaches to the live stream to see new events arrive in real time. The sequence diagram is in [`docs/architecture.md`](architecture.md#live-event-streaming).

This is the single most useful debugging tool for "the AI made a weird call" — you can see, step by step, exactly what each agent thought and did.
