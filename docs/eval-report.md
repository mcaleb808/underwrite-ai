# Eval report

_Not yet run. Trigger via `make eval` locally or the **Eval** workflow in the
Actions tab. The script writes this file in place — commit the result so
reviewers can see the latest pass rate without re-running the LLM._

Cases live in `apps/api/tests/eval/cases.yaml` and assert verdict, risk band,
premium loading bounds, required citations, and that the critic did not raise
a bias flag. Verdicts are listed as a set when domain rules allow more than
one defensible outcome.
