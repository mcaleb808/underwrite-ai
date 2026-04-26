# Evaluation

The graph is judged the way a human reviewer would judge it: run it on representative applicants and check that each decision lands inside the bounds the underwriting manual permits.

## The cases

Five golden cases in [`apps/api/tests/eval/cases.yaml`](../apps/api/tests/eval/cases.yaml), chosen to exercise the full verdict spectrum:

| # | Applicant | Profile | What it stresses |
|---|---|---|---|
| 1 | Alice — clean profile, age 29 | no declared history | the cleanest path: `accept`, low band, no loading |
| 2 | Jean — controlled hypertension, age 44 | one chronic condition, on medication | the conditional approve path with bounded loading |
| 3 | Marie — diabetes + hypertension, age 52 | two chronic conditions | the high-risk band, refer-or-conditional decision |
| 4 | Claudine — high-risk pregnancy, age 34 | gestational diabetes | UW-100: pregnancy never produces adverse loading on its own |
| 5 | Emmanuel — cardiac history, age 66 | MI, hypertension, type 2 diabetes | the very-high band, decline-or-refer territory |

Verdicts and bands are intentionally specified as *sets* (`verdict_in`, `band_in`) where domain rules allow more than one defensible outcome — a very-high-risk case may legitimately be declined *or* referred to a human, depending on the model's reasoning. The eval is strict on the things that should be deterministic, lenient on the things that involve underwriting judgment.

## What each case asserts

Per-case checks live in [`apps/api/src/scripts/run_eval.py`](../apps/api/src/scripts/run_eval.py) `_check_case()`:

- **`verdict`** — observed verdict ∈ `verdict_in` (or equals `verdict`).
- **`band`** — observed risk band ∈ `band_in` (or equals `band`).
- **`loading_min` / `loading_max`** — premium loading inside the bounds the cited rules permit.
- **`must_cite_rules`** — every named rule_id appears in `decision.citations`.
- **`must_not_cite_rules`** — none of the named rule_ids appear (guards against e.g. district being cited as adverse).
- **`must_not_flag_bias`** — the critic did not raise `bias_flag`.

A case passes only when *every* check passes. The runner prints per-case PASS/FAIL with failing-check details and exits non-zero when any case fails.

## Running it

Locally:

```bash
make eval
# or, equivalently:
cd apps/api && uv run python -m src.scripts.run_eval
```

Each run also writes a Markdown report to [`docs/eval-report.md`](eval-report.md) — pass-rate, per-case verdict / band / uplift, a Mermaid pie + latency chart, and a "where the system fell short" section that translates raw check failures into plain English ("The system's verdict didn't match what the rules call for here…").

In CI: [`.github/workflows/eval.yml`](../.github/workflows/eval.yml) is a manual-dispatch workflow that runs the suite against the deployed configuration and uploads `docs/eval-report.md` as an artifact.

## Latest results

See [`docs/eval-report.md`](eval-report.md) for the most recent run. The report is honest about what passes and what fails — the failing cases (and the precise check that failed) are listed verbatim, not glossed over. Today's pass rate is **3 of 5**; the two failures involve the critic's verdict bounds on conditional approves, documented in the report.

## What the eval doesn't catch

The golden suite checks that the graph produces *defensible* decisions on representative cases. It doesn't catch:

- silent regressions in tone or empathy (the email composer is qualitatively reviewed);
- latency tail behaviour beyond the per-case timing in the report;
- failure modes outside the verdict spectrum these five cases cover.

For deeper unit coverage of the deterministic pieces (risk scoring math, RAG chunker, event bus, route validation) see [`docs/testing.md`](testing.md).
