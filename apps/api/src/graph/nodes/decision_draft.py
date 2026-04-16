"""Draft an underwriting decision based on risk factors and guidelines."""

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict:
    return {
        "needs_revision": False,
        "events": [{"node": "decision_draft", "type": "stub"}],
    }
