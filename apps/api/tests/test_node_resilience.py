"""LLM nodes emit a graceful error event when the LLM call exhausts retries."""

from datetime import date

import pytest

from src.graph.nodes import critic as critic_node
from src.graph.nodes import decision_draft as decision_node
from src.schemas.applicant import (
    ApplicantProfile,
    Demographics,
    Lifestyle,
    Occupation,
    Vitals,
)
from src.schemas.decision import DecisionDraft


def _applicant() -> ApplicantProfile:
    return ApplicantProfile(
        applicant_id="A-TEST-1",
        demographics=Demographics(
            first_name="Test",
            last_name="Person",
            dob=date(1990, 1, 1),
            sex="F",
            email="test@example.com",
            nid="1199012345678901",
            district="Kigali",
            province="Kigali City",
            ubudehe_category=2,
            cbhi_status="enrolled",
        ),
        occupation=Occupation(title="Teacher", **{"class": "I"}),
        lifestyle=Lifestyle(tobacco="none", alcohol_units_per_week=0),
        vitals=Vitals(height_cm=165, weight_kg=60, sbp=120, dbp=80),
        declared_history=[],
        sum_insured_rwf=1_000_000,
    )


class _ThrowingChain:
    """Stand-in for the structured-output chain that always raises on invoke."""

    def with_retry(self, **_kwargs: object) -> "_ThrowingChain":
        return self

    def invoke(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("openrouter went down")


class _ThrowingLLM:
    def with_structured_output(self, _schema: type) -> _ThrowingChain:
        return _ThrowingChain()


def test_decision_draft_returns_error_event_when_llm_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(decision_node, "_llm", lambda: _ThrowingLLM())
    state = {
        "task_id": "t-fail-draft",
        "applicant": _applicant(),
        "risk_factors": [],
        "retrieved_guidelines": [],
        "risk_score": 12.0,
        "risk_band": "low",
    }

    update = decision_node.run(state)

    assert "decision" not in update
    events = update["events"]
    assert len(events) == 1
    assert events[0]["node"] == "decision_draft"
    assert events[0]["type"] == "error"
    assert "openrouter went down" in events[0]["error"]


def test_critic_returns_error_event_when_llm_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(critic_node, "_llm", lambda: _ThrowingLLM())
    draft = DecisionDraft(
        verdict="accept",
        premium_loading_pct=0,
        conditions=[],
        reasoning="ok",
        citations=[],
    )
    state = {
        "task_id": "t-fail-critic",
        "applicant": _applicant(),
        "decision": draft,
        "risk_factors": [],
        "retrieved_guidelines": [],
        "risk_score": 12.0,
        "risk_band": "low",
        "revision_count": 0,
    }

    update = critic_node.run(state)

    assert update["needs_revision"] is False
    assert update["revision_count"] == 1
    events = update["events"]
    assert len(events) == 1
    assert events[0]["node"] == "critic"
    assert events[0]["type"] == "error"
    assert "openrouter went down" in events[0]["error"]
