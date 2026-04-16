"""Adversarial review of the decision draft for accuracy and fairness."""

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict:
    return {
        "needs_revision": False,
        "revision_count": state.get("revision_count", 0) + 1,
        "events": [{"node": "critic", "type": "stub"}],
    }
