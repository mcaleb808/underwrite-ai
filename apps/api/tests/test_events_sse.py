"""SSE event-stream + event_bus tests."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import Application, Event, Task, TaskStatus
from src.services import event_bus


def _parse_sse(text: str) -> list[dict[str, Any]]:
    events = []
    for raw in text.split("\n\n"):
        raw = raw.strip()
        if raw.startswith("data: "):
            events.append(json.loads(raw[len("data: ") :]))
    return events


# -- event_bus unit tests --------------------------------------------------


@pytest.mark.asyncio
async def test_event_bus_publish_to_subscriber() -> None:
    queue = event_bus.subscribe("t1")
    try:
        await event_bus.publish("t1", {"node": "a", "type": "tick"})
        event = await asyncio.wait_for(queue.get(), timeout=1)
        assert event == {"node": "a", "type": "tick"}
    finally:
        event_bus.unsubscribe("t1", queue)


@pytest.mark.asyncio
async def test_event_bus_publish_with_no_subscribers_is_noop() -> None:
    # should not raise; nothing to assert beyond that
    await event_bus.publish("t-nobody", {"node": "a", "type": "tick"})


@pytest.mark.asyncio
async def test_event_bus_close_terminates_stream() -> None:
    received: list[Any] = []

    async def consume() -> None:
        async for event in event_bus.stream("t-close"):
            received.append(event)

    consumer_task = asyncio.create_task(consume())
    await asyncio.sleep(0.01)  # let consumer subscribe
    await event_bus.publish("t-close", {"node": "x", "type": "tick"})
    await event_bus.close("t-close")
    await asyncio.wait_for(consumer_task, timeout=1)

    assert received == [{"node": "x", "type": "tick"}]


# -- SSE route tests --------------------------------------------------------


def test_events_unknown_task_emits_error(client: TestClient) -> None:
    with client.stream("GET", "/api/v1/applications/nope/events") as resp:
        assert resp.status_code == 200
        body = resp.read().decode()
    events = _parse_sse(body)
    assert events == [{"node": "orchestrator", "type": "error", "error": "task not found"}]


def test_events_replays_history_and_closes_for_finished_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            app_row = Application(applicant_id="alice-kigali-clean", data="{}")
            session.add(app_row)
            await session.flush()
            session.add(
                Task(
                    task_id="t-finished",
                    application_id=app_row.id,
                    reference_number="UW-2026-AAA111",
                    status=TaskStatus.awaiting_review,
                )
            )
            session.add(
                Event(
                    task_id="t-finished",
                    node="risk_assessor",
                    event_type="score",
                    payload=json.dumps({"score": 42, "band": "moderate"}),
                )
            )
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(seed())
    finally:
        loop.close()

    with client.stream("GET", "/api/v1/applications/t-finished/events") as resp:
        assert resp.status_code == 200
        body = resp.read().decode()

    events = _parse_sse(body)
    assert len(events) == 2
    assert events[0]["node"] == "risk_assessor"
    assert events[0]["score"] == 42
    assert events[0]["band"] == "moderate"
    assert events[1] == {"node": "orchestrator", "type": "closed"}


def test_events_response_is_text_event_stream(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    async def seed() -> None:
        async with session_factory() as session:
            app_row = Application(applicant_id="alice", data="{}")
            session.add(app_row)
            await session.flush()
            session.add(
                Task(
                    task_id="t-mime",
                    application_id=app_row.id,
                    reference_number="UW-2026-BBB222",
                    status=TaskStatus.awaiting_review,
                )
            )
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(seed())
    finally:
        loop.close()

    with client.stream("GET", "/api/v1/applications/t-mime/events") as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
