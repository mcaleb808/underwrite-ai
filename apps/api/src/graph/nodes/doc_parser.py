"""Extract structured clinical data from medical PDFs."""

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict:
    return {"events": [{"node": "doc_parser", "type": "stub"}]}
