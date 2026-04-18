"""Request and response schemas for the public API."""

from datetime import datetime
from typing import Literal

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
    email_status: str | None = None
    approved_by: str | None = None
    created_at: datetime
    updated_at: datetime


Verdict = Literal["accept", "accept_with_conditions", "refer", "decline"]


class ModifyDecisionRequest(BaseModel):
    verdict: Verdict | None = None
    premium_loading_pct: float | None = None
    conditions: list[str] | None = None
    reasoning: str | None = None


class ApproveRequest(BaseModel):
    approved_by: str
    notify_email: str | None = None  # falls back to applicant.demographics.email


class ApproveResponse(BaseModel):
    status: str
    email_status: str
    provider_message_id: str | None = None


class ReevalRequest(BaseModel):
    note: str | None = None


class ReevalResponse(BaseModel):
    task_id: str
    status: str
