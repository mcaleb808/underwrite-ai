"""Request and response schemas for the public API."""

from datetime import datetime

from pydantic import BaseModel

from src.schemas.decision import RiskFactor


class CreateApplicationResponse(BaseModel):
    task_id: str
    reference_number: str
    status: str
    status_url: str


class DecisionResponse(BaseModel):
    verdict: str
    premium_loading_pct: float
    conditions: list[str]
    reasoning: str
    citations: list[str]


class ApplicationStatusResponse(BaseModel):
    task_id: str
    reference_number: str
    status: str
    risk_score: float | None
    risk_band: str | None
    risk_factors: list[RiskFactor] = []
    decision: DecisionResponse | None
    created_at: datetime
    updated_at: datetime
