"""Compute deterministic risk score from applicant + parsed medical."""

from typing import Any

from src.graph.state import UnderwritingState
from src.schemas.events import RiskAssessorScored
from src.services.log import bind_node, get_logger
from src.services.tracing import tracer
from src.tools.risk_scoring import assess_risk

log = get_logger(__name__)


def run(state: UnderwritingState) -> dict[str, Any]:
    bind_node(state, "risk_assessor")
    with tracer().start_as_current_span("node.risk_assessor"):
        profile = state["applicant"]
        parsed = state.get("parsed_medical") or []
        result = assess_risk(profile, parsed)
        log.info(
            "node_end",
            status="done",
            score=result.score,
            band=result.band,
            factor_count=len(result.factors),
        )
        return {
            "risk_score": result.score,
            "risk_band": result.band,
            "risk_factors": result.factors,
            "events": [
                RiskAssessorScored(
                    score=result.score,
                    band=result.band,
                    factor_count=len(result.factors),
                )
            ],
        }
