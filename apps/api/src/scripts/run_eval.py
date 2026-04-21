"""Run the underwriting graph against golden cases and report pass/fail."""

from __future__ import annotations

import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from src.graph.builder import build_graph
from src.schemas.applicant import ApplicantProfile

ROOT = Path(__file__).resolve().parent.parent.parent
APPLICANTS_DIR = ROOT / "src" / "data" / "applicants"
CASES_FILE = ROOT / "tests" / "eval" / "cases.yaml"
REPORT_FILE = ROOT.parent.parent / "docs" / "eval-report.md"

Verdict = Literal["accept", "accept_with_conditions", "refer", "decline"]
Band = Literal["low", "moderate", "high", "very_high"]


class Expected(BaseModel):
    verdict: Verdict | None = None
    verdict_in: list[Verdict] | None = None
    band: Band | None = None
    band_in: list[Band] | None = None
    loading_min: float | None = None
    loading_max: float | None = None
    must_cite_rules: list[str] = Field(default_factory=list)
    must_not_cite_rules: list[str] = Field(default_factory=list)
    must_not_flag_bias: bool = True


class Case(BaseModel):
    name: str
    applicant_file: str
    expected: Expected


class Suite(BaseModel):
    cases: list[Case]


class CheckResult(BaseModel):
    label: str
    passed: bool
    detail: str = ""


class CaseResult(BaseModel):
    name: str
    verdict: str
    band: str
    loading: float
    citations: list[str]
    bias_flag: bool
    duration_ms: int
    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def _check_case(expected: Expected, observed: CaseResult) -> list[CheckResult]:
    checks: list[CheckResult] = []

    allowed_verdicts = expected.verdict_in or ([expected.verdict] if expected.verdict else None)
    if allowed_verdicts:
        ok = observed.verdict in allowed_verdicts
        checks.append(
            CheckResult(
                label="verdict",
                passed=ok,
                detail=f"got {observed.verdict}, expected one of {allowed_verdicts}",
            )
        )

    allowed_bands = expected.band_in or ([expected.band] if expected.band else None)
    if allowed_bands:
        ok = observed.band in allowed_bands
        checks.append(
            CheckResult(
                label="band",
                passed=ok,
                detail=f"got {observed.band}, expected one of {allowed_bands}",
            )
        )

    if expected.loading_min is not None:
        ok = observed.loading >= expected.loading_min
        checks.append(
            CheckResult(
                label="loading_min",
                passed=ok,
                detail=f"got {observed.loading}, expected >= {expected.loading_min}",
            )
        )
    if expected.loading_max is not None:
        ok = observed.loading <= expected.loading_max
        checks.append(
            CheckResult(
                label="loading_max",
                passed=ok,
                detail=f"got {observed.loading}, expected <= {expected.loading_max}",
            )
        )

    for rule in expected.must_cite_rules:
        ok = rule in observed.citations
        checks.append(
            CheckResult(
                label=f"cites {rule}",
                passed=ok,
                detail="" if ok else f"{rule} not in {observed.citations}",
            )
        )

    for rule in expected.must_not_cite_rules:
        ok = rule not in observed.citations
        checks.append(
            CheckResult(
                label=f"does not cite {rule}",
                passed=ok,
                detail="" if ok else f"{rule} unexpectedly cited",
            )
        )

    if expected.must_not_flag_bias:
        ok = not observed.bias_flag
        checks.append(
            CheckResult(label="no bias flag", passed=ok, detail="critic raised bias_flag")
        )

    return checks


def _run_one(case: Case) -> CaseResult:
    applicant_path = APPLICANTS_DIR / case.applicant_file
    profile = ApplicantProfile.model_validate_json(applicant_path.read_text())

    graph = build_graph()
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    started = time.perf_counter()
    state = graph.invoke(
        {"task_id": f"eval-{case.name}", "applicant": profile, "events": []},
        config,
    )
    duration_ms = round((time.perf_counter() - started) * 1000)

    decision = state["decision"]
    critique = state.get("critique")
    observed = CaseResult(
        name=case.name,
        verdict=str(decision.verdict),
        band=str(state["risk_band"]),
        loading=float(decision.premium_loading_pct),
        citations=list(decision.citations),
        bias_flag=bool(critique and critique.bias_flag),
        duration_ms=duration_ms,
        checks=[],
    )
    observed.checks = _check_case(case.expected, observed)
    return observed


def _render_report(results: list[CaseResult]) -> str:
    pass_count = sum(1 for r in results if r.passed)
    total = len(results)
    pct = (pass_count / total * 100) if total else 0.0
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# Eval report",
        "",
        f"**{pass_count}/{total} cases passing ({pct:.0f}%)** — last run {now}.",
        "",
        "Cases assert verdict, risk band, premium loading bounds, required",
        "citations, and that the critic did not raise a bias flag. Verdicts",
        "are listed as a set when domain rules allow more than one defensible",
        "outcome.",
        "",
        "| Case | Verdict | Band | Load% | Bias | Duration | Result |",
        "|------|---------|------|-------|------|----------|--------|",
    ]
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        bias = "yes" if r.bias_flag else "no"
        lines.append(
            f"| {r.name} | {r.verdict} | {r.band} | {r.loading:.1f} | {bias} |"
            f" {r.duration_ms} ms | {status} |"
        )

    failed = [r for r in results if not r.passed]
    if failed:
        lines.extend(["", "## Failures", ""])
        for r in failed:
            lines.append(f"### {r.name}")
            lines.append("")
            for c in r.checks:
                if c.passed:
                    continue
                lines.append(f"- **{c.label}** — {c.detail}")
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    suite = Suite.model_validate(yaml.safe_load(CASES_FILE.read_text()))

    results: list[CaseResult] = []
    print(f"Running {len(suite.cases)} eval case(s)...\n")
    for case in suite.cases:
        result = _run_one(case)
        marker = "PASS" if result.passed else "FAIL"
        print(f"  {marker:4s}  {case.name}  ({result.duration_ms} ms)")
        for check in result.checks:
            if not check.passed:
                print(f"          - {check.label}: {check.detail}")
        results.append(result)

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(_render_report(results))
    print(f"\nReport written to {REPORT_FILE.relative_to(ROOT.parent.parent)}")

    pass_count = sum(1 for r in results if r.passed)
    print(f"\n{pass_count}/{len(results)} cases passed.")
    return 0 if pass_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
