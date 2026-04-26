"""Typed event payloads emitted by the underwriting graph."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class _BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True)


class DocParserParsed(_BaseEvent):
    node: Literal["doc_parser"] = "doc_parser"
    type: Literal["parsed"] = "parsed"
    doc_count: int
    error_count: int


class RiskAssessorScored(_BaseEvent):
    node: Literal["risk_assessor"] = "risk_assessor"
    type: Literal["score"] = "score"
    score: float
    band: str
    factor_count: int


class GuidelinesRetrieved(_BaseEvent):
    node: Literal["guidelines_rag"] = "guidelines_rag"
    type: Literal["retrieved"] = "retrieved"
    chunk_count: int
    rule_ids: list[str]


class DecisionDrafted(_BaseEvent):
    node: Literal["decision_draft"] = "decision_draft"
    type: Literal["drafted"] = "drafted"
    verdict: str
    premium_loading_pct: float
    citations: list[str]
    is_revision: bool


class DecisionDraftError(_BaseEvent):
    node: Literal["decision_draft"] = "decision_draft"
    type: Literal["error"] = "error"
    error: str
    is_revision: bool


class CriticReviewed(_BaseEvent):
    node: Literal["critic"] = "critic"
    type: Literal["reviewed"] = "reviewed"
    issue_count: int
    bias_flag: bool
    needs_revision: bool
    regex_issue_count: int


class CriticSkipped(_BaseEvent):
    node: Literal["critic"] = "critic"
    type: Literal["skipped"] = "skipped"
    reason: str


class CriticError(_BaseEvent):
    node: Literal["critic"] = "critic"
    type: Literal["error"] = "error"
    error: str


class OrchestratorStarted(_BaseEvent):
    node: Literal["orchestrator"] = "orchestrator"
    type: Literal["started"] = "started"


class OrchestratorUsage(_BaseEvent):
    node: Literal["orchestrator"] = "orchestrator"
    type: Literal["usage"] = "usage"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    calls: int


class OrchestratorError(_BaseEvent):
    node: Literal["orchestrator"] = "orchestrator"
    type: Literal["error"] = "error"
    error: str


class OrchestratorFinalized(_BaseEvent):
    node: Literal["orchestrator"] = "orchestrator"
    type: Literal["finalized"] = "finalized"
    verdict: str | None = None
    risk_score: float | None = None


class OrchestratorClosed(_BaseEvent):
    node: Literal["orchestrator"] = "orchestrator"
    type: Literal["closed"] = "closed"


NodeEvent = Annotated[
    Union[  # noqa: UP007 - Annotated needs an explicit Union
        DocParserParsed,
        RiskAssessorScored,
        GuidelinesRetrieved,
        DecisionDrafted,
        DecisionDraftError,
        CriticReviewed,
        CriticSkipped,
        CriticError,
    ],
    Field(discriminator="type"),
]

OrchestratorEvent = Annotated[
    Union[  # noqa: UP007
        OrchestratorStarted,
        OrchestratorUsage,
        OrchestratorError,
        OrchestratorFinalized,
        OrchestratorClosed,
    ],
    Field(discriminator="type"),
]
