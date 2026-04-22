"""Run the underwriting graph for a task and persist + publish its events."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DecisionRecord, Event, Task, TaskStatus
from src.db.session import async_session
from src.graph.builder import build_graph
from src.schemas.applicant import ApplicantProfile
from src.schemas.events import (
    OrchestratorError,
    OrchestratorFinalized,
    OrchestratorStarted,
    OrchestratorUsage,
)
from src.services import event_bus
from src.services.log import bind, get_logger, graph_callbacks, llm_observability, unbind
from src.services.tracing import tracer

log = get_logger(__name__)

# Per-task cancel signals. Set by request_cancel(); the graph loop checks
# between chunks and unwinds gracefully when signalled.
_cancel_events: dict[str, asyncio.Event] = {}


def request_cancel(task_id: str) -> bool:
    """Signal a running task to stop. Returns True if the task was known."""
    event = _cancel_events.get(task_id)
    if event is None:
        return False
    event.set()
    return True


def _to_dict(event: BaseModel | dict[str, Any]) -> dict[str, Any]:
    return event.model_dump() if isinstance(event, BaseModel) else event


async def _persist_event(
    session: AsyncSession, task_id: str, event: BaseModel | dict[str, Any]
) -> None:
    payload = _to_dict(event)
    session.add(
        Event(
            task_id=task_id,
            node=str(payload.get("node", "unknown")),
            event_type=str(payload.get("type", "unknown")),
            payload=json.dumps(payload, default=str),
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
    bind(task_id=task_id)
    started = time.perf_counter()
    log.info("graph_start", doc_count=len(doc_paths))

    graph = build_graph()
    config = {
        "configurable": {"thread_id": task_id},
        "callbacks": graph_callbacks(),
    }
    llm_observability.reset_task(task_id)
    cancel_event = asyncio.Event()
    _cancel_events[task_id] = cancel_event

    with tracer().start_as_current_span(
        "underwriting.run",
        attributes={
            "langfuse.session.id": applicant.applicant_id,
            "langfuse.user.id": applicant.applicant_id,
            "underwriting.task_id": task_id,
            "underwriting.doc_count": len(doc_paths),
        },
    ) as span:
        try:
            async with async_session() as session:
                await _set_status(session, task_id, TaskStatus.running)
                await session.commit()
            await event_bus.publish(task_id, _to_dict(OrchestratorStarted()))

            try:
                cancelled = False
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
                                await event_bus.publish(task_id, _to_dict(event))
                        await session.commit()
                    usage = llm_observability.get_usage(task_id)
                    usage_event = OrchestratorUsage(
                        prompt_tokens=int(usage["prompt_tokens"]),
                        completion_tokens=int(usage["completion_tokens"]),
                        total_tokens=int(usage["total_tokens"]),
                        cost_usd=float(usage["cost_usd"]),
                        calls=int(usage["calls"]),
                    )
                    await event_bus.publish(task_id, _to_dict(usage_event))

                    if cancel_event.is_set():
                        cancelled = True
                        break

                if cancelled:
                    log.warning("graph_cancelled")
                    span.set_attribute("underwriting.cancelled", True)
                    cancel_evt = OrchestratorError(error="cancelled by user")
                    async with async_session() as session:
                        await _persist_event(session, task_id, cancel_evt)
                        await _set_status(session, task_id, TaskStatus.cancelled)
                        await session.commit()
                    await event_bus.publish(task_id, _to_dict(cancel_evt))
                    await event_bus.close(task_id)
                    return

                snapshot = await graph.aget_state(config)
                final: dict[str, Any] = snapshot.values
            except Exception as exc:
                log.exception("graph_end", status="failed", error=repr(exc))
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, repr(exc)))
                err_event = OrchestratorError(error=repr(exc))
                async with async_session() as session:
                    await _persist_event(session, task_id, err_event)
                    await _set_status(session, task_id, TaskStatus.failed)
                    await session.commit()
                await event_bus.publish(task_id, _to_dict(err_event))
                await event_bus.close(task_id)
                return

            async with async_session() as session:
                decision = final.get("decision")
                if decision is not None:
                    await _persist_decision(session, task_id, decision)

                task = (
                    await session.execute(select(Task).where(Task.task_id == task_id))
                ).scalar_one()
                task.risk_score = final.get("risk_score")
                task.risk_band = final.get("risk_band")
                factors = final.get("risk_factors") or []
                task.risk_factors_json = json.dumps(
                    [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in factors]
                )
                task.status = (
                    TaskStatus.awaiting_review if decision is not None else TaskStatus.failed
                )
                await session.commit()

            if decision is not None:
                span.set_attribute("underwriting.verdict", str(decision.verdict))
            if final.get("risk_score") is not None:
                span.set_attribute("underwriting.risk_score", float(final["risk_score"]))
            if final.get("risk_band") is not None:
                span.set_attribute("underwriting.risk_band", str(final["risk_band"]))
            span.set_attribute("underwriting.revision_count", int(final.get("revision_count", 0)))
            span.set_status(Status(StatusCode.OK))

            log.info(
                "graph_end",
                status="done",
                verdict=getattr(decision, "verdict", None),
                risk_score=final.get("risk_score"),
            )

            await event_bus.publish(
                task_id,
                _to_dict(
                    OrchestratorFinalized(
                        verdict=getattr(decision, "verdict", None),
                        risk_score=final.get("risk_score"),
                    )
                ),
            )
            await event_bus.close(task_id)
        finally:
            log.info(
                "graph_duration",
                duration_ms=round((time.perf_counter() - started) * 1000),
                **llm_observability.get_usage(task_id),
            )
            llm_observability.discard_task(task_id)
            _cancel_events.pop(task_id, None)
            unbind("task_id")


__all__ = ["request_cancel", "run_task"]
