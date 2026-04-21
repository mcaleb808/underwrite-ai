"""Schema-level tests for the typed event payloads."""

import pytest
from pydantic import ValidationError

from src.schemas.events import (
    CriticReviewed,
    DecisionDrafted,
    DocParserParsed,
    GuidelinesRetrieved,
    OrchestratorFinalized,
    OrchestratorStarted,
    OrchestratorUsage,
    RiskAssessorScored,
)


def test_doc_parser_dump_shape() -> None:
    payload = DocParserParsed(doc_count=2, error_count=0).model_dump()
    assert payload == {"node": "doc_parser", "type": "parsed", "doc_count": 2, "error_count": 0}


def test_decision_drafted_requires_revision_flag() -> None:
    with pytest.raises(ValidationError):
        DecisionDrafted(
            verdict="accept",
            premium_loading_pct=0,
            citations=[],
            # is_revision missing
        )


def test_orchestrator_started_has_no_extra_fields() -> None:
    payload = OrchestratorStarted().model_dump()
    assert payload == {"node": "orchestrator", "type": "started"}


def test_orchestrator_finalized_allows_null_fields() -> None:
    payload = OrchestratorFinalized().model_dump()
    assert payload == {
        "node": "orchestrator",
        "type": "finalized",
        "verdict": None,
        "risk_score": None,
    }


def test_orchestrator_usage_full_shape() -> None:
    payload = OrchestratorUsage(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.0001,
        calls=1,
    ).model_dump()
    assert payload["node"] == "orchestrator"
    assert payload["type"] == "usage"
    assert payload["total_tokens"] == 15


def test_critic_reviewed_full_shape() -> None:
    payload = CriticReviewed(
        issue_count=2,
        bias_flag=False,
        needs_revision=True,
        regex_issue_count=0,
    ).model_dump()
    assert payload["node"] == "critic"
    assert payload["type"] == "reviewed"


def test_event_models_are_immutable() -> None:
    event = RiskAssessorScored(score=12.0, band="low", factor_count=3)
    with pytest.raises(ValidationError):
        event.score = 99.0  # type: ignore[misc]


def test_guidelines_retrieved_rule_ids_required() -> None:
    with pytest.raises(ValidationError):
        GuidelinesRetrieved(chunk_count=5)  # type: ignore[call-arg]
