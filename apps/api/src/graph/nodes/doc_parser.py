"""Extract structured clinical data from medical PDFs."""

from typing import Any

from src.graph.state import UnderwritingState


def run(state: UnderwritingState) -> dict[str, Any]:
    return {"events": [{"node": "doc_parser", "type": "stub"}]}
