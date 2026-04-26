# Anticipated questions

15 questions a thoughtful reviewer is likely to ask after the demo, with talking-point answers. Each answer is short on purpose — these are notes for *you* speaking, not paragraphs to recite.

If a question isn't here and you don't know the answer, say *"I don't know — the honest answer is I'd need to check"*. Don't bluff.

---

### 1. Why LangGraph specifically? Why not just a sequence of LLM calls in a script?

- The graph is a **typed state machine**, not a script — every node has a defined input/output contract via a TypedDict.
- LangGraph gives me **parallel branches** (`risk_assessor` and `guidelines_rag` run concurrently after the parser) and **conditional routing** (the critic can send the draft back for revision) for free.
- The state contract uses **append-only reducers** for the lists multiple branches contribute to — no race conditions, no clobbering.
- Streaming + checkpointing are built-in, which is what feeds the live event timeline in the dashboard.
- See [`docs/architecture.md`](architecture.md) — the state contract section.

### 2. How do you stop the AI from making biased decisions?

Two layers, on purpose:

- **Soft layer (LLM):** the drafter's system prompt explicitly forbids citing Ubudehe category, CBHI status, or district as adverse factors. The critic has the same forbiddances and looks for them in the draft.
- **Hard layer (regex):** the region adapter (`adapters/rw.py`) runs a deterministic regex over the reasoning and conditions of every adverse decision. If `ubudehe`, `mutuelle`, `cbhi`, or `district-without-endemic-context` appears, the draft goes back for revision regardless of what the LLM thought.
- The LLM may miss bias. The regex cannot. That's the point.

### 3. Your eval shows 3 of 5 cases passing — why are you showing that publicly?

- The eval doesn't earn its keep if it lies. Hiding failures is worse than the failures themselves.
- The two failures are **bounded and documented** in `docs/eval-report.md` — both are verdict-band edge cases on conditional approves, not safety failures. The bias-flag check passes on every case.
- Honest reporting is a feature of a real engineering process. A glowing "5/5" eval would suggest I gamed the bounds.

### 4. What stops the model from inventing a rule ID that doesn't exist in the manual?

- The drafter's system prompt requires citations to come from the **retrieved chunks** in `state["retrieved_guidelines"]` — not from prior knowledge.
- The critic explicitly checks for this — failure mode #3 is "cited rule_ids do not appear in the retrieved guidelines". If a phantom rule appears, the critic flags it and the draft goes back for revision.
- The eval has a `must_not_cite_rules` assertion for cases where a specific (real) rule shouldn't appear as adverse — guarding against e.g. district loadings.

### 5. Why is the risk scorer pure Python? Couldn't an LLM do it?

- A risk score has to be **reproducible**. Same input → same output, every time. LLMs aren't good at that.
- It also has to be **auditable**. Every contribution to the 0–100 score is a named line — "Age 31–45: +15.0", "BMI overweight: +10.0". A human reviewer can read that and disagree with a specific contribution. They can't disagree with an opaque LLM number.
- And it's faster and free.
- See [`tools/risk_scoring.py`](../apps/api/src/tools/risk_scoring.py).

### 6. How does this scale to, say, 10,000 cases per day?

Three answers depending on how serious the question is:

- **For 10k/day**: it already runs on Cloud Run, which auto-scales horizontally. The current bottleneck is concurrent LLM calls per instance, not the application code. Bumping `max_instance_count` and provisioning more LLM credit is the whole change.
- **For multi-host scale**: the in-process event_bus is the only thing that's currently single-process. The interface is `subscribe / publish / close`; swapping to Redis pub/sub behind the same surface is a one-PR change.
- **For database scale**: SQLite is the current store. PostgreSQL with the same SQLAlchemy models is the next step; the app is fully async with `aiosqlite` today, switching to `asyncpg` is a connection-string change.

### 7. What's the cost per case today?

- A clean run (no critic revision) is roughly 4-5k tokens across 3 LLM calls — well under $0.001 in the dashboard's cost pill, even with strong-model rates.
- A revision pass roughly doubles that.
- The expensive case in the demo (Jean) is about $0.0008.
- Real cost depends on the model — `STRONG_MODEL` and `FAST_MODEL` are configurable. The composer uses the fast model for the customer email so the most-frequent path stays cheap.

### 8. What about PHI? Are you compliant with anything?

- **Today, no compliance claim.** The seed data is synthetic. Production deployment to a real insurer would require, at minimum, BAA-equivalent contracts with the model providers, encryption-at-rest verification on the storage layers, an access-audit trail, and a data-residency review.
- The architecture supports those: secrets are in GCP Secret Manager (not in env), all events are persisted with timestamps and a request ID for audit, and the LLM provider is swappable through a single base URL.
- This is in scope for "what I'd build next", not what's deployed today.

### 9. Why OpenRouter as the model gateway instead of going direct?

- One API key for many providers — Anthropic, OpenAI, Google, Mistral all behind the same `base_url`. Swapping models is a config change.
- LangChain's `ChatOpenAI` works against any OpenAI-compatible endpoint, so OpenRouter slots in without changing the application code.
- Token usage and cost data come back in the same shape, which is what the in-process cost counter and the `/metrics` endpoint depend on.
- One place to manage rate limits and budgets per model.

### 10. The underwriter modifies a decision — does the system learn from those edits?

- **Today, no.** Modifications are persisted (the `decisions` table records `approved_by` and the modified content), but they don't feed back into the prompts or any fine-tuning loop.
- Why not yet: with five test cases and synthetic data, there's nothing meaningful to learn from. Building a feedback loop on noise produces a worse system, not a better one.
- The natural next step at real volume: collect modifications, look for patterns ("the LLM keeps overshooting on hypertension loadings"), then either tune the prompt, adjust the deterministic scorer, or add a new pinned guideline rule. That's a deliberate human review step, not auto-tuning.

### 11. What if the critic and the drafter never agree?

- Hard cap: `MAX_REVISIONS = 2` in [`graph/routing.py`](../apps/api/src/graph/routing.py). After two revision passes the latest draft is finalized regardless of what the critic still thinks.
- The critic's outstanding issues are surfaced in the dashboard as "issues remaining", so the human reviewer sees the disagreement explicitly before approving.
- The critic is a **signal**, not a veto — by design. A real underwriter wouldn't accept a system where one of two LLMs gets unilateral final say.

### 12. How do you trust the model's reasoning paragraph? Couldn't it be a post-hoc rationalisation?

- It almost certainly is, on some cases — that's the nature of LLM-generated reasoning.
- That's why the **citations** matter more than the prose. Every cited rule ID is verified against the retrieved guidelines (the critic checks this). Every premium loading has to map to a cited rule.
- The reasoning is for *human readability*, not for trust. Trust comes from the deterministic risk score, the regex bias check, the cited-rule constraint, and the eval — not from the prose.

### 13. You said scale-to-zero — what's the cold-start cost?

- About 3-6 seconds for the first request after the service has been idle. Subsequent requests within the warm window are sub-100ms for everything except the LLM calls.
- It's the right tradeoff for the use pattern: underwriters work in deliberate review sessions, not at constant low background. Idle cost is zero, peak cost is a few seconds of latency.
- For an always-warm posture, `min_instances=1` flips it — about $5–10/month on a small Cloud Run instance.

### 14. What was the hardest thing you debugged?

- The Langfuse trace silence on Cloud Run. Local development showed perfect nested traces; the production deploy was silent. The synchronous diagnostic span exported fine — it was specifically LangChain callback spans inside FastAPI's `BackgroundTask` context that vanished before any OTel processor saw them.
- I built a token-gated diagnostic endpoint to confirm the export pipeline was healthy in prod, narrowed it to a context-propagation interaction between LangChain and the OTel SDK in the BackgroundTask runtime combo, and made the call to ship local-only traces rather than chase a deeper fix before the deadline.
- The whole investigation is in the commit history (PRs #38, #39, #40). Honest engineering means knowing when to stop optimising and ship.

### 15. With two more weeks, what's next?

Three things, in priority order:

1. **A custom application form.** Today the dashboard runs five seed personas. Letting underwriters submit a real `ApplicantProfile` + their own PDFs is the next obvious step.
2. **An Alembic baseline migration.** `Base.metadata.create_all` was the right shortcut for the demo; it's not the right shape for any real schema evolution.
3. **A second region adapter** to validate the protocol seam isn't accidentally Rwanda-shaped. Even a half-finished Kenya or Uganda adapter would catch assumptions baked into `rw.py` that I can't see today.
- See the *What I'd build next* section in [`docs/architecture.md`](architecture.md) for the full list.

---

## Holding-pattern phrases (memorise these)

For when a question lands and you need a beat to think:

- *"Great question — the short answer is X. The longer answer is..."*
- *"Two ways to think about that..."*
- *"I want to be honest — that's a known limitation. Here's what would change if I had more time..."*
- *"I don't know off the top of my head. Let me show you where that lives in the code."* (then open the file)

For when you genuinely don't know:

- *"That's outside what I tested. My instinct is X but I'd want to verify before I commit to it."*

Don't say *"I think"* unless you mean it. Don't say *"basically"* — it's filler.
