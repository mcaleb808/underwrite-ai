"""Compute deterministic risk score from applicant + parsed medical."""

from typing import Any

from src.graph.state import UnderwritingState
from src.tools.risk_scoring import assess_risk


def run(state: UnderwritingState) -> dict[str, Any]:
    profile = state["applicant"]
    parsed = state.get("parsed_medical") or []
    result = assess_risk(profile, parsed)
    return {
        "risk_score": result.score,
        "risk_band": result.band,
        "risk_factors": result.factors,
        "events": [
            {
                "node": "risk_assessor",
                "type": "score",
                "score": result.score,
                "band": result.band,
                "factor_count": len(result.factors),
            }
        ],
    }
