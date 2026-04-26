"""UnderwritingState - the contract every graph node must respect."""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from src.schemas.applicant import ApplicantProfile
from src.schemas.decision import Critique, DecisionDraft, GuidelineChunk, RiskFactor
from src.schemas.medical import ParsedMedicalRecord

Verdict = Literal["accept", "accept_with_conditions", "refer", "decline"]


class UnderwritingState(TypedDict, total=False):
    # -- inputs (set once by orchestrator) --
    task_id: str
    applicant: ApplicantProfile
    medical_doc_paths: list[str]

    # -- doc parser output --
    parsed_medical: Annotated[list[ParsedMedicalRecord], add]

    # -- risk assessor output --
    risk_score: float  # 0-100
    risk_band: Literal["low", "moderate", "high", "very_high"]
    risk_factors: list[RiskFactor]

    # -- guidelines rag output --
    retrieved_guidelines: list[GuidelineChunk]

    # -- decision + critic loop --
    decision: DecisionDraft | None
    critique: Critique | None
    needs_revision: bool
    revision_count: int

    # -- streaming / observability --
    messages: Annotated[list[AnyMessage], add_messages]
    events: Annotated[list[dict], add]
    errors: Annotated[list[str], add]
