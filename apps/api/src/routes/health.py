"""Operational endpoints: /health for liveness, /metrics for at-a-glance counters."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import DecisionRecord, Task, TaskStatus
from src.db.session import get_session
from src.rag.ingest import _collection
from src.services.log import llm_observability

router = APIRouter(prefix="/api/v1", tags=["ops"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    db: Literal["ok", "error"]
    chroma: Literal["ok", "empty", "error"]
    llm_provider: Literal["configured", "missing"]


class MetricsResponse(BaseModel):
    decisions_total: int
    decisions_failed: int
    tasks_total: int
    total_tokens_since_start: int
    total_cost_usd_since_start: float
    llm_calls_since_start: int


async def _check_db(session: AsyncSession) -> Literal["ok", "error"]:
    try:
        await session.execute(select(1))
        return "ok"
    except Exception:
        return "error"


def _check_chroma() -> Literal["ok", "empty", "error"]:
    try:
        count = _collection(settings.CHROMA_DIR).count()
        return "ok" if count > 0 else "empty"
    except Exception:
        return "error"


def _check_llm_provider() -> Literal["configured", "missing"]:
    return "configured" if settings.OPENROUTER_API_KEY else "missing"


@router.get("/health", response_model=HealthResponse)
async def health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HealthResponse:
    db = await _check_db(session)
    chroma = _check_chroma()
    llm = _check_llm_provider()
    overall: Literal["ok", "degraded"] = (
        "ok" if db == "ok" and chroma == "ok" and llm == "configured" else "degraded"
    )
    return HealthResponse(status=overall, db=db, chroma=chroma, llm_provider=llm)


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MetricsResponse:
    decisions_total = (await session.execute(select(func.count(DecisionRecord.id)))).scalar_one()
    decisions_failed = (
        await session.execute(select(func.count(Task.id)).where(Task.status == TaskStatus.failed))
    ).scalar_one()
    tasks_total = (await session.execute(select(func.count(Task.id)))).scalar_one()

    usage = llm_observability.get_lifetime_usage()
    return MetricsResponse(
        decisions_total=int(decisions_total),
        decisions_failed=int(decisions_failed),
        tasks_total=int(tasks_total),
        total_tokens_since_start=int(usage["total_tokens"]),
        total_cost_usd_since_start=float(usage["cost_usd"]),
        llm_calls_since_start=int(usage["calls"]),
    )
