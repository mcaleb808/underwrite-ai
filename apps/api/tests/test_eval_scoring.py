"""Pure-Python tests for the eval-suite scorer (no LLM required)."""

from src.scripts.run_eval import CaseResult, Expected, Suite, _check_case, _render_report


def _observed(**overrides: object) -> CaseResult:
    base: dict[str, object] = {
        "name": "test",
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
    passing = _observed(name="alice")
    failing = _observed(
        name="bob",
        verdict="decline",
        checks=[],
    )
    failing.checks = _check_case(Expected(verdict_in=["accept"]), failing)

    report = _render_report([passing, failing])

    assert "1/2 cases passing (50%)" in report
    assert "alice" in report and "bob" in report
    assert "## Failures" in report
    assert "verdict" in report


def test_yaml_schema_round_trips() -> None:
    raw = {
        "cases": [
            {
                "name": "x",
                "applicant_file": "x.json",
                "expected": {"verdict_in": ["accept"], "band": "low"},
            }
        ]
    }
    suite = Suite.model_validate(raw)
    assert suite.cases[0].expected.verdict_in == ["accept"]
    assert suite.cases[0].expected.must_not_flag_bias is True
