"""Conditional edges for the underwriting graph."""

from src.graph.state import UnderwritingState

MAX_REVISIONS = 2


def route_after_critic(state: UnderwritingState) -> str:
    if state.get("needs_revision") and state.get("revision_count", 0) < MAX_REVISIONS:
        return "revise"
    return "finalize"
