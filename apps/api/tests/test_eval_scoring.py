"""Pure-Python tests for the eval-suite scorer (no LLM required)."""

from src.scripts.run_eval import (
    CaseResult,
    Expected,
    Suite,
    _check_case,
    _humanize_check,
    _humanize_verdict,
    _render_report,
)


def _observed(**overrides: object) -> CaseResult:
    base: dict[str, object] = {
        "name": "test",
        "label": "Test — sample case",
        "verdict": "accept",
        "band": "low",
        "loading": 0.0,
        "citations": ["UW-130"],
        "bias_flag": False,
        "duration_ms": 100,
        "checks": [],
    }
    base.update(overrides)
    return CaseResult(**base)


def test_verdict_in_passes_when_verdict_matches() -> None:
    expected = Expected(verdict_in=["accept", "accept_with_conditions"])
    checks = _check_case(expected, _observed(verdict="accept_with_conditions"))
    verdict_check = next(c for c in checks if c.label == "verdict")
    assert verdict_check.passed


def test_verdict_in_fails_when_verdict_outside_set() -> None:
    expected = Expected(verdict_in=["accept"])
    checks = _check_case(expected, _observed(verdict="decline"))
    verdict_check = next(c for c in checks if c.label == "verdict")
    assert not verdict_check.passed
    assert "decline" in verdict_check.detail


def test_loading_bounds_enforced() -> None:
    expected = Expected(loading_max=10, loading_min=2)
    checks = _check_case(expected, _observed(loading=15))
    labels = {c.label: c for c in checks}
    assert not labels["loading_max"].passed
    assert labels["loading_min"].passed


def test_must_cite_rule_missing_fails() -> None:
    expected = Expected(must_cite_rules=["UW-040"])
    checks = _check_case(expected, _observed(citations=["UW-130"]))
    cite_check = next(c for c in checks if c.label == "cites UW-040")
    assert not cite_check.passed


def test_bias_flag_blocks_pass() -> None:
    expected = Expected()
    checks = _check_case(expected, _observed(bias_flag=True))
    bias_check = next(c for c in checks if c.label == "no bias flag")
    assert not bias_check.passed


def test_render_report_shows_pass_count_and_failures() -> None:
    passing = _observed(name="alice", label="Alice — clean")
    failing = _observed(
        name="bob",
        label="Bob — high risk",
        verdict="decline",
        checks=[],
    )
    failing.checks = _check_case(Expected(verdict_in=["accept"]), failing)

    report = _render_report([passing, failing])

    assert "1 out of 2 cases passing" in report
    assert "Alice — clean" in report and "Bob — high risk" in report
    assert "## Where the system fell short" in report
    assert "didn't match what the rules call for" in report
    # mermaid charts are present
    assert "```mermaid" in report
    assert "pie showData" in report
    assert "xychart-beta" in report


def test_yaml_schema_round_trips() -> None:
    raw = {
        "cases": [
            {
                "name": "x",
                "label": "X — sample",
                "applicant_file": "x.json",
                "expected": {"verdict_in": ["accept"], "band": "low"},
            }
        ]
    }
    suite = Suite.model_validate(raw)
    assert suite.cases[0].expected.verdict_in == ["accept"]
    assert suite.cases[0].label == "X — sample"
    assert suite.cases[0].expected.must_not_flag_bias is True


def test_humanize_verdict_maps_known_values() -> None:
    assert _humanize_verdict("accept") == "Approve"
    assert _humanize_verdict("accept_with_conditions") == "Approve with conditions"
    assert _humanize_verdict("decline") == "Decline"
    # unknown value falls back to a readable form
    assert _humanize_verdict("special_case") == "Special case"


def test_humanize_check_explains_known_failure_types() -> None:
    assert "verdict didn't match" in _humanize_check("verdict", "got x, expected y")
    assert "bias flag" in _humanize_check("no bias flag", "")
    assert "premium uplift" in _humanize_check("loading_max", "got 50, expected <= 30")
    assert "UW-040" in _humanize_check("cites UW-040", "")
