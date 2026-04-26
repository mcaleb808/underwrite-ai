# Agents and prompts

Five small specialists make up the underwriting pipeline. They run in a fixed order, each has one job, and each hands the next one a tidy bundle of facts. This page walks through what each one does and why it's built the way it is.

If you just want a one-line summary: **two of the five agents are plain Python (no AI), three call a language model with a strict output schema, and the critic gets to send the draft back for one revision.**

---

## The five agents at a glance

| Order | Agent | What it does | How |
|---|---|---|---|
| 1 | `doc_parser` | reads the medical PDFs | calls a fast LLM, returns structured facts |
| 2a | `risk_assessor` | turns facts into a 0–100 risk score | plain Python — no AI |
| 2b | `guidelines_rag` | looks up the relevant rules from the manual | semantic search (no AI) |
| 3 | `decision_draft` | writes the underwriting decision | calls a strong LLM, schema-validated |
| 4 | `critic` | challenges the decision for fairness and accuracy | strong LLM + a regex safety net |

Steps **2a** and **2b** run in parallel after the parser finishes. The critic can ask the drafter to try again — but only once.

---

## Walking through each agent

### 1. `doc_parser` — the chart-reader

Takes the applicant's medical PDFs and pulls the structured facts out of them: lab values, diagnoses, blood-pressure readings. It uses a fast (cheap) language model and is told to **copy values verbatim** and never invent anything that isn't in the document. If a field isn't in the chart, it stays empty.

Each PDF is parsed independently, so one bad scan doesn't break the rest of the run.

📁 [`apps/api/src/graph/nodes/doc_parser.py`](../apps/api/src/graph/nodes/doc_parser.py)

### 2a. `risk_assessor` — the calculator

Pure Python. No AI. Given the applicant profile and the parsed facts, it adds up a risk score (0–100) by walking through fixed rules: age bracket adds X, BMI band adds Y, controlled hypertension adds Z, and so on. Each contribution is recorded so a human reviewer can see exactly *why* the score is what it is.

The reason this is deterministic and not LLM-driven: a risk score has to be reproducible. Run the same applicant through the same code twice and you must get the same number. LLMs aren't good at that.

📁 [`apps/api/src/graph/nodes/risk_assessor.py`](../apps/api/src/graph/nodes/risk_assessor.py), math in [`tools/risk_scoring.py`](../apps/api/src/tools/risk_scoring.py)

### 2b. `guidelines_rag` — the rule-finder

The underwriting manual has 15 numbered rules (UW-001 through UW-140). For each application, this agent figures out which rules are relevant — using semantic search over the manual — and forwards them to the drafter. It also *always* includes four foundational rules (district/endemic loading, equity guard, score-to-verdict mapping, fairness checks), even if the search wouldn't have surfaced them, so the drafter can never accidentally ignore them.

📁 [`apps/api/src/graph/nodes/guidelines_rag.py`](../apps/api/src/graph/nodes/guidelines_rag.py)

### 3. `decision_draft` — the underwriter

This is where the AI actually makes the call. The drafter sees the applicant profile, the risk score, the risk factors, and the relevant rules — and it writes an underwriting decision: a verdict (approve / approve with conditions / refer / decline), a premium loading percentage, a list of conditions, the reasoning, and the rule IDs it used.

Two things the drafter is *never* allowed to do, baked into its instructions:

- cite Ubudehe category, CBHI status, or district as a *reason* to load a premium or deny coverage (these are protected attributes);
- invent a percentage — every premium loading has to come from a cited rule.

The output is validated against a Pydantic schema (`DecisionDraft`), so the verdict has to be one of the four allowed values, the loading has to be a number, and the citations have to be a list of strings. Garbage out is structurally impossible.

📁 [`apps/api/src/graph/nodes/decision_draft.py`](../apps/api/src/graph/nodes/decision_draft.py)

### 4. `critic` — the second opinion

Once the drafter produces a decision, the critic challenges it. It's another LLM call, but with a different system prompt — its job is to find things wrong. It checks five concrete failure modes:

1. does the verdict actually match the score?
2. did the reasoning lean on protected terms (Ubudehe / CBHI / district)?
3. were any cited rule IDs *not* in the retrieved guidelines?
4. did the loading exceed what the cited rules permit?
5. does each condition actually have evidence to back it up?

The critic's findings are then *combined* with a deterministic regex check that scans the draft for protected terms. If either the LLM or the regex flags a problem, the draft goes back to the drafter for one more attempt — capped at one revision so a stubborn loop can't run forever.

📁 [`apps/api/src/graph/nodes/critic.py`](../apps/api/src/graph/nodes/critic.py), regex backstop in [`adapters/rw.py`](../apps/api/src/adapters/rw.py)

### 5. The email composer (post-pipeline)

Strictly speaking this isn't part of the graph — it runs when an underwriter clicks **Approve & notify applicant**. But it has the same structured-output + fallback shape as the agents above, so it belongs here.

The composer turns the (technical) decision into a (warm, plain-English) customer email. Its system prompt forbids leaking any internal vocabulary: no rule IDs, no "verdict" / "score" / "loading" jargon, no raw verdict enum values, no numeric percentages. If the LLM call fails for any reason, a deterministic template fires so the customer never receives an empty email.

📁 [`apps/api/src/services/email/composer.py`](../apps/api/src/services/email/composer.py)

---

## Why every LLM call is wrapped the same way

You'll see this pattern repeated across all four LLM-using agents:

```python
ChatOpenAI(..., timeout=60, callbacks=llm_callbacks())
  .with_structured_output(SomeSchema)
  .with_retry(stop_after_attempt=2, wait_exponential_jitter=True)
```

Three things are happening:

- **`timeout=60`** — if the model takes more than a minute, give up rather than hang.
- **`with_structured_output(SomeSchema)`** — the model has to return JSON that matches a Pydantic schema, or LangChain rejects it. Verdicts can't be free-text.
- **`with_retry(...)`** — if the call fails (network blip, rate limit, schema validation error), retry once with a small jittered backoff before giving up.

If a node still fails after the retry, it converts the exception into a typed event (e.g. `DecisionDraftError`) and the failure shows up in the timeline — the run doesn't crash, it just lands in an honest failed state.

📁 representative example: [`graph/nodes/decision_draft.py`](../apps/api/src/graph/nodes/decision_draft.py)

---

## Which model does which job

Models are wired through [`apps/api/src/config.py`](../apps/api/src/config.py) and routed through OpenRouter so swapping providers is one line.

| Used for | Setting | What we run today |
|---|---|---|
| Reasoning, decision drafting, critic | `STRONG_MODEL` | a Sonnet-class model |
| Document extraction, email prose | `FAST_MODEL` | a small/fast model |

Strong-vs-fast routing follows the obvious rule: when the output is a verdict that affects someone's coverage, pay for the smarter model. When it's "copy the BMI off this PDF", a small one is fine.
