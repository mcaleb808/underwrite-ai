"""Retrieve relevant underwriting guidelines based on conditions."""

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict:
    return {"events": [{"node": "guidelines_rag", "type": "stub"}]}
