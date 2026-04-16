"""Draft an underwriting decision based on risk factors and guidelines."""

from typing import Any

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict[str, Any]:
    return {
        "needs_revision": False,
        "events": [{"node": "decision_draft", "type": "stub"}],
    }
