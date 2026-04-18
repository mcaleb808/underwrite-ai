"""Run the underwriting graph for a task and persist its outcome."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DecisionRecord, Event, Task, TaskStatus
from src.db.session import async_session
from src.graph.builder import build_graph
from src.schemas.applicant import ApplicantProfile

log = logging.getLogger(__name__)


async def _persist_events(
    session: AsyncSession, task_id: str, events: list[dict[str, Any]]
) -> None:
    for ev in events:
        session.add(
            Event(
                task_id=task_id,
                node=str(ev.get("node", "unknown")),
                event_type=str(ev.get("type", "unknown")),
                payload=json.dumps(ev, default=str),
            )
        )


async def _persist_decision(session: AsyncSession, task_id: str, draft: Any) -> None:
    record = DecisionRecord(
        task_id=task_id,
        verdict=str(draft.verdict),
        premium_loading_pct=float(draft.premium_loading_pct),
        conditions=json.dumps(list(draft.conditions)),
        reasoning=str(draft.reasoning),
        citations=json.dumps(list(draft.citations)),
    )
    session.add(record)


async def _set_status(session: AsyncSession, task_id: str, status: TaskStatus) -> None:
    task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one()
    task.status = status


async def run_task(task_id: str, applicant: ApplicantProfile, doc_paths: list[str]) -> None:
    """Execute the underwriting graph for a single task and persist results."""
    graph = build_graph()
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}

    async with async_session() as session:
        await _set_status(session, task_id, TaskStatus.running)
        await session.commit()

    try:
        result = await graph.ainvoke(
            {
                "task_id": task_id,
                "applicant": applicant,
                "medical_doc_paths": doc_paths,
                "events": [],
            },
            config,
        )
    except Exception as exc:
        log.exception("graph failed for task %s", task_id)
        async with async_session() as session:
            session.add(
                Event(
                    task_id=task_id,
                    node="orchestrator",
                    event_type="error",
                    payload=json.dumps({"error": repr(exc)}),
                )
            )
            await _set_status(session, task_id, TaskStatus.failed)
            await session.commit()
        return

    async with async_session() as session:
        await _persist_events(session, task_id, list(result.get("events") or []))
        decision = result.get("decision")
        if decision is not None:
            await _persist_decision(session, task_id, decision)

        task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one()
        task.risk_score = result.get("risk_score")
        task.risk_band = result.get("risk_band")
        task.status = TaskStatus.awaiting_review if decision is not None else TaskStatus.failed
        await session.commit()
