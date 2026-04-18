"""Run the underwriting graph for a task and persist + publish its events."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DecisionRecord, Event, Task, TaskStatus
from src.db.session import async_session
from src.graph.builder import build_graph
from src.schemas.applicant import ApplicantProfile
from src.services import event_bus

log = logging.getLogger(__name__)


async def _persist_event(session: AsyncSession, task_id: str, event: dict[str, Any]) -> None:
    session.add(
        Event(
            task_id=task_id,
            node=str(event.get("node", "unknown")),
            event_type=str(event.get("type", "unknown")),
            payload=json.dumps(event, default=str),
        )
    )


async def _persist_decision(session: AsyncSession, task_id: str, draft: Any) -> None:
    session.add(
        DecisionRecord(
            task_id=task_id,
            verdict=str(draft.verdict),
            premium_loading_pct=float(draft.premium_loading_pct),
            conditions=json.dumps(list(draft.conditions)),
            reasoning=str(draft.reasoning),
            citations=json.dumps(list(draft.citations)),
        )
    )


async def _set_status(session: AsyncSession, task_id: str, status: TaskStatus) -> None:
    task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one()
    task.status = status


async def run_task(task_id: str, applicant: ApplicantProfile, doc_paths: list[str]) -> None:
    """Stream the graph for a task: persist + publish each node event live."""
    graph = build_graph()
    config = {"configurable": {"thread_id": task_id}}

    async with async_session() as session:
        await _set_status(session, task_id, TaskStatus.running)
        await session.commit()
    await event_bus.publish(task_id, {"node": "orchestrator", "type": "started"})

    try:
        async for chunk in graph.astream(
            {
                "task_id": task_id,
                "applicant": applicant,
                "medical_doc_paths": doc_paths,
                "events": [],
            },
            config,
            stream_mode="updates",
        ):
            async with async_session() as session:
                for _, update in chunk.items():
                    for event in update.get("events") or []:
                        await _persist_event(session, task_id, event)
                        await event_bus.publish(task_id, event)
                await session.commit()

        snapshot = await graph.aget_state(config)
        final: dict[str, Any] = snapshot.values
    except Exception as exc:
        log.exception("graph failed for task %s", task_id)
        async with async_session() as session:
            await _persist_event(
                session, task_id, {"node": "orchestrator", "type": "error", "error": repr(exc)}
            )
            await _set_status(session, task_id, TaskStatus.failed)
            await session.commit()
        await event_bus.publish(
            task_id, {"node": "orchestrator", "type": "error", "error": repr(exc)}
        )
        await event_bus.close(task_id)
        return

    async with async_session() as session:
        decision = final.get("decision")
        if decision is not None:
            await _persist_decision(session, task_id, decision)

        task = (await session.execute(select(Task).where(Task.task_id == task_id))).scalar_one()
        task.risk_score = final.get("risk_score")
        task.risk_band = final.get("risk_band")
        factors = final.get("risk_factors") or []
        task.risk_factors_json = json.dumps(
            [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in factors]
        )
        task.status = TaskStatus.awaiting_review if decision is not None else TaskStatus.failed
        await session.commit()

    await event_bus.publish(
        task_id,
        {
            "node": "orchestrator",
            "type": "finalized",
            "verdict": getattr(decision, "verdict", None),
            "risk_score": final.get("risk_score"),
        },
    )
    await event_bus.close(task_id)


__all__ = ["run_task"]
