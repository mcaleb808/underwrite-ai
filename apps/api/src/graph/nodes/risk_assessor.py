"""Compute risk score from parsed medical data and applicant profile."""

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict:
    return {"events": [{"node": "risk_assessor", "type": "stub"}]}
