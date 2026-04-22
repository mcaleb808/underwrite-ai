"""Retrieve relevant underwriting guideline chunks from Chroma.

Pins foundational rules (district endemic, equity, score-to-verdict, critic
checks) so the decision_draft and critic always see them, even when the
applicant's case-specific query wouldn't surface them.
"""

from typing import Any

from src.config import settings
from src.graph.state import UnderwritingState
from src.rag.retriever import retrieve
from src.schemas.decision import GuidelineChunk
from src.schemas.events import GuidelinesRetrieved
from src.services.log import bind_node, get_logger
from src.services.tracing import tracer

log = get_logger(__name__)

# Always present in the prompt — every decision is governed by these.
_PINNED_RULES = ("UW-070", "UW-090", "UW-130", "UW-140")


def _build_query(state: UnderwritingState) -> str:
    parts: list[str] = []
    profile = state.get("applicant")
    if profile is not None:
        parts.extend(profile.declared_history)
        parts.append(f"occupation {profile.occupation.title}")
        parts.append(f"sum insured {profile.sum_insured_rwf}")
    for factor in state.get("risk_factors") or []:
        # factor.name like "htn_controlled" or "bmi_overweight"
        parts.append(factor.name.replace("_", " "))
    return " | ".join(parts) if parts else "underwriting decision general"


def _retrieve_rule(rule_id: str) -> GuidelineChunk | None:
    """Fetch a specific rule by id via a targeted query. Cheap, deterministic."""
    hits = retrieve(rule_id, settings.CHROMA_DIR, k=3)
    return next((h for h in hits if h.rule_id == rule_id), None)


def run(state: UnderwritingState) -> dict[str, Any]:
    bind_node(state, "guidelines_rag")
    with tracer().start_as_current_span("node.guidelines_rag"):
        query = _build_query(state)
        semantic = retrieve(query, settings.CHROMA_DIR, k=6)

        seen = {c.rule_id for c in semantic}
        pinned: list[GuidelineChunk] = []
        for rule_id in _PINNED_RULES:
            if rule_id in seen:
                continue
            chunk = _retrieve_rule(rule_id)
            if chunk is not None:
                pinned.append(chunk)
                seen.add(rule_id)

        chunks = semantic + pinned
        log.info(
            "node_end",
            status="done",
            semantic_count=len(semantic),
            pinned_count=len(pinned),
            rule_ids=[c.rule_id for c in chunks],
        )
        return {
            "retrieved_guidelines": chunks,
            "events": [
                GuidelinesRetrieved(
                    chunk_count=len(chunks),
                    rule_ids=[c.rule_id for c in chunks],
                )
            ],
        }
