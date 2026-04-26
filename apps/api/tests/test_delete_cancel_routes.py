"""Tests for the delete + cancel lifecycle endpoints."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import Application, DecisionRecord, Event, Task, TaskStatus

ALICE = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "data"
    / "applicants"
    / "alice-kigali-clean.json"
)


def _seed(
    session_factory: async_sessionmaker,
    task_id: str,
    *,
    status: TaskStatus,
    applicant_id: str = "alice-kigali-clean",
    reference: str = "UW-2026-XXX",
    with_decision: bool = True,
) -> None:
    async def go() -> None:
        async with session_factory() as session:
            existing = (
                await session.execute(
                    select(Application).where(Application.applicant_id == applicant_id)
                )
            ).scalar_one_or_none()
            if existing is None:
                app_row = Application(applicant_id=applicant_id, data=ALICE.read_text())
                session.add(app_row)
                await session.flush()
                app_id = app_row.id
            else:
                app_id = existing.id
            session.add(
                Task(
                    task_id=task_id,
                    application_id=app_id,
                    reference_number=reference,
                    status=status,
                )
            )
            if with_decision:
                session.add(
                    DecisionRecord(
                        task_id=task_id,
                        verdict="accept",
                        premium_loading_pct=0.0,
                        conditions=json.dumps([]),
                        reasoning="r",
                        citations=json.dumps([]),
                    )
                )
            session.add(
                Event(task_id=task_id, node="doc_parser", event_type="parsed", payload="{}")
            )
            await session.commit()

    asyncio.get_event_loop().run_until_complete(go())


def _count_rows(session_factory: async_sessionmaker, model) -> int:
    from sqlalchemy import func

    async def go() -> int:
        async with session_factory() as session:
            return (await session.execute(select(func.count(model.id)))).scalar_one()

    return asyncio.get_event_loop().run_until_complete(go())


def test_delete_task_removes_related_rows(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed(session_factory, "t-del", status=TaskStatus.awaiting_review)

    response = client.delete("/api/v1/applications/t-del")
    assert response.status_code == 204

    assert _count_rows(session_factory, Task) == 0
    assert _count_rows(session_factory, DecisionRecord) == 0
    assert _count_rows(session_factory, Event) == 0
    # Orphan application should also be gone.
    assert _count_rows(session_factory, Application) == 0


def test_delete_task_keeps_application_when_other_tasks_reference_it(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed(session_factory, "t-keep-a", status=TaskStatus.awaiting_review, reference="UW-A")
    _seed(session_factory, "t-keep-b", status=TaskStatus.sent, reference="UW-B")

    client.delete("/api/v1/applications/t-keep-a")

    assert _count_rows(session_factory, Task) == 1
    assert _count_rows(session_factory, Application) == 1


def test_delete_rejects_running_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed(session_factory, "t-busy", status=TaskStatus.running)

    response = client.delete("/api/v1/applications/t-busy")
    assert response.status_code == 409
    assert _count_rows(session_factory, Task) == 1


def test_delete_missing_task_returns_404(client: TestClient) -> None:
    assert client.delete("/api/v1/applications/ghost").status_code == 404


def test_clear_terminal_wipes_finished_and_keeps_running(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed(session_factory, "t-done-1", status=TaskStatus.sent, reference="UW-1")
    _seed(
        session_factory,
        "t-done-2",
        status=TaskStatus.failed,
        reference="UW-2",
        with_decision=False,
    )
    _seed(
        session_factory,
        "t-busy",
        status=TaskStatus.running,
        reference="UW-3",
        with_decision=False,
    )

    response = client.delete("/api/v1/applications")
    assert response.status_code == 204

    remaining = asyncio.get_event_loop().run_until_complete(
        _load_all_task_ids(session_factory),
    )
    assert remaining == ["t-busy"]


async def _load_all_task_ids(session_factory: async_sessionmaker) -> list[str]:
    async with session_factory() as session:
        rows = (await session.execute(select(Task.task_id).order_by(Task.task_id))).all()
    return [r[0] for r in rows]


def test_cancel_signals_running_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    from src.services import orchestrator

    _seed(session_factory, "t-stop", status=TaskStatus.running, with_decision=False)
    # Register a cancel event the way run_task() would.
    orchestrator._cancel_events["t-stop"] = asyncio.Event()

    response = client.post("/api/v1/applications/t-stop/cancel")
    assert response.status_code == 202
    assert orchestrator._cancel_events["t-stop"].is_set()

    orchestrator._cancel_events.pop("t-stop", None)


def test_cancel_rejects_terminal_status(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed(session_factory, "t-done", status=TaskStatus.sent)

    response = client.post("/api/v1/applications/t-done/cancel")
    assert response.status_code == 409


def test_cancel_missing_task_returns_404(client: TestClient) -> None:
    assert client.post("/api/v1/applications/ghost/cancel").status_code == 404


def test_cancel_force_cancels_orphan_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    from src.services import orchestrator

    _seed(session_factory, "t-orphan", status=TaskStatus.running, with_decision=False)
    orchestrator._cancel_events.pop("t-orphan", None)

    response = client.post("/api/v1/applications/t-orphan/cancel")
    assert response.status_code == 202
    assert response.json() == {"status": "cancelled"}

    async def fetch() -> tuple[TaskStatus, list[tuple[str, str]]]:
        async with session_factory() as session:
            task = (
                await session.execute(select(Task).where(Task.task_id == "t-orphan"))
            ).scalar_one()
            events = (
                await session.execute(
                    select(Event.node, Event.event_type).where(Event.task_id == "t-orphan")
                )
            ).all()
            return task.status, [(n, t) for n, t in events]

    status, events = asyncio.get_event_loop().run_until_complete(fetch())
    assert status is TaskStatus.cancelled
    assert ("orchestrator", "error") in events
