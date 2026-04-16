"""Compute risk score from parsed medical data and applicant profile."""

from typing import Any

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict[str, Any]:
    return {"events": [{"node": "risk_assessor", "type": "stub"}]}
