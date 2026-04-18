"""Tests for the human-in-the-loop review actions."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import Application, DecisionRecord, Task, TaskStatus

ALICE = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "data"
    / "applicants"
    / "alice-kigali-clean.json"
)


def _seed(
    session_factory: async_sessionmaker,
    *,
    status: TaskStatus = TaskStatus.awaiting_review,
) -> str:
    async def go() -> str:
        async with session_factory() as session:
            app_row = Application(applicant_id="alice-kigali-clean", data=ALICE.read_text())
            session.add(app_row)
            await session.flush()
            session.add(
                Task(
                    task_id="t-review",
                    application_id=app_row.id,
                    reference_number="UW-2026-AAA111",
                    status=status,
                    risk_score=1.0,
                    risk_band="low",
                )
            )
            session.add(
                DecisionRecord(
                    task_id="t-review",
                    verdict="accept",
                    premium_loading_pct=0.0,
                    conditions=json.dumps([]),
                    reasoning="Initial reasoning.",
                    citations=json.dumps(["UW-010", "UW-020"]),
                )
            )
            await session.commit()
        return "t-review"

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(go())
    finally:
        loop.close()


def test_modify_decision_updates_fields_and_status(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    task_id = _seed(session_factory)
    response = client.patch(
        f"/api/v1/applications/{task_id}/decision",
        json={
            "verdict": "accept_with_conditions",
            "premium_loading_pct": 15.0,
            "conditions": ["Provide updated lab results within 30 days"],
            "reasoning": "Underwriter override after manual review.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "modified"
    assert body["decision"]["verdict"] == "accept_with_conditions"
    assert body["decision"]["premium_loading_pct"] == 15.0
    assert body["decision"]["conditions"] == ["Provide updated lab results within 30 days"]


def test_modify_decision_404_when_task_missing(client: TestClient) -> None:
    response = client.patch("/api/v1/applications/missing/decision", json={"verdict": "accept"})
    assert response.status_code == 404


def test_approve_sends_email_and_marks_sent(
    client: TestClient,
    session_factory: async_sessionmaker,
    fake_email,
) -> None:
    task_id = _seed(session_factory)
    response = client.post(
        f"/api/v1/applications/{task_id}/approve",
        json={"approved_by": "underwriter@demo"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sent"
    assert body["email_status"] == "sent"
    assert body["provider_message_id"] == "fake-1"

    assert len(fake_email.sent) == 1
    msg = fake_email.sent[0]
    assert msg.to == "alice.uwase+demo@example.com"
    assert "UW-2026-AAA111" in msg.subject
    assert "Alice Uwase" in msg.html

    # status endpoint reflects approval
    status = client.get(f"/api/v1/applications/{task_id}").json()
    assert status["status"] == "sent"
    assert status["approved_by"] == "underwriter@demo"
    assert status["email_status"] == "sent"


def test_approve_uses_override_email_when_provided(
    client: TestClient,
    session_factory: async_sessionmaker,
    fake_email,
) -> None:
    task_id = _seed(session_factory)
    response = client.post(
        f"/api/v1/applications/{task_id}/approve",
        json={"approved_by": "uw@demo", "notify_email": "override@example.com"},
    )
    assert response.status_code == 200
    assert fake_email.sent[0].to == "override@example.com"


def test_approve_rejects_running_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    task_id = _seed(session_factory, status=TaskStatus.running)
    response = client.post(f"/api/v1/applications/{task_id}/approve", json={"approved_by": "uw"})
    assert response.status_code == 409


def test_reeval_kicks_off_orchestrator_and_clears_decision(
    client: TestClient,
    session_factory: async_sessionmaker,
    stub_orchestrator: list,
) -> None:
    task_id = _seed(session_factory)
    response = client.post(f"/api/v1/applications/{task_id}/reeval", json={"note": "lab corrected"})
    assert response.status_code == 200, response.text
    assert response.json() == {"task_id": task_id, "status": "reeval"}

    assert len(stub_orchestrator) == 1
    assert stub_orchestrator[0][0] == task_id

    # decision row should be gone until next graph run produces one
    status = client.get(f"/api/v1/applications/{task_id}").json()
    assert status["decision"] is None
    assert status["status"] == "reeval"


def test_reeval_rejects_running_task(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    task_id = _seed(session_factory, status=TaskStatus.running)
    response = client.post(f"/api/v1/applications/{task_id}/reeval", json={})
    assert response.status_code == 409
