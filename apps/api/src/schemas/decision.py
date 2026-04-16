from typing import Literal

from pydantic import BaseModel


class RiskFactor(BaseModel):
    name: str  # e.g. "age_band_46_55"
    weight: float  # weight in model 0..1
    value: float  # observed value 0..100
    contribution: float  # weight * value
    source: Literal["declared", "parsed_medical", "district", "computed"]
    evidence: str | None = None


class GuidelineChunk(BaseModel):
    rule_id: str  # UW-030
    section_title: str
    text: str
    score: float  # chroma similarity


Verdict = Literal["accept", "accept_with_conditions", "refer", "decline"]


class DecisionDraft(BaseModel):
    verdict: Verdict
    premium_loading_pct: float = 0
    conditions: list[str] = []
    reasoning: str
    citations: list[str]  # rule_ids


class Critique(BaseModel):
    issues: list[str]
    needs_revision: bool
    suggestions: list[str]
    bias_flag: bool = False
