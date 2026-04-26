# Agents and prompts

Five nodes make up the underwriting graph. Two are deterministic Python; three call an LLM with a Pydantic-typed structured output. The graph is wired in [`apps/api/src/graph/builder.py`](../apps/api/src/graph/builder.py); the per-node code lives in [`apps/api/src/graph/nodes/`](../apps/api/src/graph/nodes/).

## Node-by-node

### `doc_parser` — fast LLM, structured output

[`apps/api/src/graph/nodes/doc_parser.py`](../apps/api/src/graph/nodes/doc_parser.py) · model: `FAST_MODEL`

Extracts structured clinical facts from medical PDFs into the `ParsedMedicalRecord` schema. The system prompt orders the model to copy values verbatim, leave fields empty when absent, and constrain enums (`flag` ∈ `high|low|normal`, `status` ∈ `active|controlled|resolved`). Each PDF is parsed in isolation (`_parse_one`); a single failed extraction is recorded as an error and the batch continues.

### `risk_assessor` — deterministic Python (no LLM)

[`apps/api/src/graph/nodes/risk_assessor.py`](../apps/api/src/graph/nodes/risk_assessor.py), scoring math in [`apps/api/src/tools/risk_scoring.py`](../apps/api/src/tools/risk_scoring.py)

Pure-Python scoring keeps the score auditable and reproducible. Inputs: applicant profile + parsed medical records. Output: `risk_score` (0–100), `risk_band`, list of `RiskFactor`s with attributable `contribution` values. The LLM never touches this node — that is the point.

### `guidelines_rag` — RAG retrieval (no LLM)

[`apps/api/src/graph/nodes/guidelines_rag.py`](../apps/api/src/graph/nodes/guidelines_rag.py)

Builds a query from the applicant's declared history, occupation, sum insured, and the named risk factors, then runs Chroma cosine similarity (`text-embedding-3-small`) and unions the top-6 hits with four pinned foundational rules (`UW-070`, `UW-090`, `UW-130`, `UW-140`). Pinning came out of an earlier failure mode — the drafter cited universally-applicable rules that hadn't been retrieved.

### `decision_draft` — strong LLM, structured output

[`apps/api/src/graph/nodes/decision_draft.py`](../apps/api/src/graph/nodes/decision_draft.py) · model: `STRONG_MODEL`

System prompt encodes the hard underwriting contract:

- map score → verdict per UW-130 unless a hard rule overrides (UW-040 HbA1c > 8.5, UW-060 active TB, UW-050 non-adherent HIV);
- never cite Ubudehe, CBHI, or district as adverse factors (UW-090, UW-140);
- premium loadings must come from cited rules — no invented percentages.

User message stitches together the applicant profile, score + band, risk factors, retrieved guideline chunks, and (on a revision pass) the critic's outstanding issues + suggestions. Output is `DecisionDraft` via `with_structured_output(DecisionDraft)`.

### `critic` — strong LLM + deterministic regex

[`apps/api/src/graph/nodes/critic.py`](../apps/api/src/graph/nodes/critic.py) · model: `STRONG_MODEL`

Adversarial review in two layers. The LLM audits the draft against five concrete failure modes (verdict ↔ score mismatch, bias terms, uncited rules, loading-cap violations, conditions without supporting evidence) and returns a `Critique`. That is then *unioned* with the deterministic regex backstop in [`adapters/rw.py`](../apps/api/src/adapters/rw.py) (`_BIAS_TERMS`) — so even if the LLM thinks the draft is clean, a regex match flips `needs_revision = True`. LLM may miss bias; regex cannot.

If the critic raises issues and `revision_count < 2`, control routes back to `decision_draft` for one more pass with the critic's notes appended; otherwise the draft is finalized. The cap and routing live in [`graph/routing.py`](../apps/api/src/graph/routing.py).

### Email composer — fast LLM, structured output, template fallback

[`apps/api/src/services/email/composer.py`](../apps/api/src/services/email/composer.py) · model: `FAST_MODEL` · `temperature=0.4`

Customer-facing message. The system prompt sets a tight tone-by-verdict guide and a long list of hard prohibitions: no rule IDs, no `verdict`/`score`/`loading` vocabulary, no raw verdict enum, no numeric percentages, no internal reasoning paragraph. Output is `ComposedEmail` (subject + body, length-validated). On any LLM failure the deterministic `_fallback()` template fires so an approval never ships an empty email.

## Resilience

Every LLM call goes through the same wrapper:

```python
ChatOpenAI(..., timeout=60, callbacks=llm_callbacks())
  .with_structured_output(SomeSchema)
  .with_retry(stop_after_attempt=2, wait_exponential_jitter=True)
```

Representative example: [`graph/nodes/decision_draft.py:29-37, 90-94`](../apps/api/src/graph/nodes/decision_draft.py). The `with_retry` is on the *invoke chain* (after `with_structured_output`), so retries cover both transport errors and validation failures. On final exhaustion each node converts the exception into a typed event (e.g. `DecisionDraftError`) so the failure shows up in the timeline rather than crashing the run.

## Models

Set in [`apps/api/src/config.py`](../apps/api/src/config.py). `STRONG_MODEL` is used for decision drafting and critic review; `FAST_MODEL` for document parsing and email composition. Both flow through the same OpenRouter base URL so swapping providers is a one-line config change.

| Use | Setting | Default |
|---|---|---|
| Reasoning, structured output | `STRONG_MODEL` | a Sonnet-class model |
| Extraction, prose | `FAST_MODEL` | a small/fast model |
