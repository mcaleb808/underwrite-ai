# Evaluation — how do we know the AI is doing the right thing?

Unit tests can prove that a function returns the right number. They cannot prove that an AI made a defensible underwriting decision. So the AI gets a separate test of its own: a small set of representative applicants, run end-to-end through the real graph, with the resulting decisions checked against bounds a human underwriter would expect.

The same way a junior underwriter is judged on real (anonymised) cases, this AI is judged on five synthetic ones.

---

## The five test applicants

Each applicant covers a different point on the risk spectrum, so the eval exercises the full verdict range:

| Applicant | Profile | What this case stresses |
|---|---|---|
| **Alice** — age 29 | clean profile, no declared history | the cleanest path: approve, low risk, no premium loading |
| **Jean** — age 44 | controlled hypertension, on medication | the conditional-approve path with a bounded loading |
| **Marie** — age 52 | diabetes + hypertension | high-risk band, refer-or-conditional decision |
| **Claudine** — age 34 | high-risk pregnancy | UW-100 — pregnancy never produces adverse loading on its own |
| **Emmanuel** — age 66 | cardiac history, hypertension, type 2 diabetes | very-high band, decline-or-refer territory |

Cases live in [`apps/api/tests/eval/cases.yaml`](../apps/api/tests/eval/cases.yaml).

---

## What we check on each one

For each applicant, the eval runs the full pipeline and asks five questions:

1. **Verdict** — did the system land on a defensible call (approve, approve with conditions, refer, or decline)? Verdicts are specified as a *set* — `[refer, accept_with_conditions]` — wherever the underwriting manual leaves room for legitimate disagreement.
2. **Risk band** — does the assessed band match the applicant's profile? (E.g. a 66-year-old with a cardiac history must land in `very_high`.)
3. **Premium uplift** — is the loading percentage inside the bounds the cited rules permit? Some cases assert *both* a minimum and a maximum.
4. **Cited rules** — did the decision cite the specific rule IDs a human reviewer would expect? And, just as important, did it *avoid* citing ones it shouldn't (e.g. district as adverse)?
5. **Fairness** — did the critic raise a `bias_flag`? On these cases, the answer must always be no — the inputs don't legitimately warrant one.

A case passes only when *every* check passes. The check logic lives in [`apps/api/src/scripts/run_eval.py`](../apps/api/src/scripts/run_eval.py) (`_check_case`).

---

## Running it

Locally:

```bash
make eval
# or, equivalently:
cd apps/api && uv run python -m src.scripts.run_eval
```

You'll see PASS/FAIL per case in the terminal, with the failing-check details printed inline. A Markdown report is written to [`docs/eval-report.md`](eval-report.md): pass-rate, per-case verdict / band / uplift, a Mermaid pie chart, a latency chart, and a "where the system fell short" section that translates raw check failures into plain English ("The system's verdict didn't match what the rules call for here…").

In CI: [`.github/workflows/eval.yml`](../.github/workflows/eval.yml) is a manual-dispatch workflow that runs the suite against the deployed configuration and uploads the report as a build artifact.

---

## What today's results look like

See [`docs/eval-report.md`](eval-report.md) for the most recent run. The current pass rate is **3 of 5**, and the report is honest about the two failures — they're listed by name, with the precise check that didn't pass. We don't gloss them over, because that defeats the entire point of running the eval in the first place.

---

## What this catches — and what it doesn't

The eval catches:

- a verdict landing outside the allowed set;
- a risk band off by a tier;
- a loading above or below what the rules permit;
- a missing or forbidden rule citation;
- a false bias flag on a clean case.

It doesn't catch:

- silent regressions in tone or empathy of the customer email (those are reviewed qualitatively);
- latency tail behaviour beyond the per-case timing in the report;
- failure modes outside the verdict spectrum these five cases cover.

For the deterministic pieces — risk-scoring math, RAG chunker, event-bus semantics, route validation — the unit-test layer in [`docs/testing.md`](testing.md) does the heavy lifting.
