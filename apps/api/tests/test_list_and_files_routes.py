"""Tests for list applications and per-task file routes."""

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


def _seed_tasks(session_factory: async_sessionmaker) -> None:
    async def go() -> None:
        async with session_factory() as session:
            app_row = Application(applicant_id="alice-kigali-clean", data=ALICE.read_text())
            session.add(app_row)
            await session.flush()
            for i in range(3):
                session.add(
                    Task(
                        task_id=f"t-{i}",
                        application_id=app_row.id,
                        reference_number=f"UW-2026-LIST{i}",
                        status=TaskStatus.awaiting_review,
                        risk_score=float(i * 10),
                        risk_band="low",
                    )
                )
            session.add(
                DecisionRecord(
                    task_id="t-1",
                    verdict="accept",
                    premium_loading_pct=0.0,
                    conditions=json.dumps([]),
                    reasoning="ok",
                    citations=json.dumps([]),
                )
            )
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(go())
    finally:
        loop.close()


def test_list_applications_returns_recent(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed_tasks(session_factory)
    response = client.get("/api/v1/applications")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 3
    assert {b["task_id"] for b in body} == {"t-0", "t-1", "t-2"}
    by_id = {b["task_id"]: b for b in body}
    assert by_id["t-1"]["verdict"] == "accept"
    assert by_id["t-0"]["verdict"] is None
    assert by_id["t-1"]["applicant_id"] == "alice-kigali-clean"


def test_list_applications_respects_limit(
    client: TestClient, session_factory: async_sessionmaker
) -> None:
    _seed_tasks(session_factory)
    response = client.get("/api/v1/applications?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_files_empty_when_no_uploads(client: TestClient) -> None:
    response = client.get("/api/v1/applications/no-uploads/files")
    assert response.status_code == 200
    assert response.json() == []


def test_list_and_get_file_for_uploaded_pdf(client: TestClient, tmp_path: Path) -> None:
    # The client fixture sets UPLOAD_DIR to tmp_path / "uploads"
    upload_dir = tmp_path / "uploads" / "task-with-files"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / "scan.pdf").write_bytes(b"%PDF-1.4 fake content")

    listing = client.get("/api/v1/applications/task-with-files/files")
    assert listing.status_code == 200
    assert listing.json() == ["scan.pdf"]

    download = client.get("/api/v1/applications/task-with-files/files/scan.pdf")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content == b"%PDF-1.4 fake content"


def test_get_file_blocks_path_traversal(client: TestClient, tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads" / "trav-task"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / "ok.pdf").write_bytes(b"ok")

    response = client.get("/api/v1/applications/trav-task/files/..%2f..%2fetc%2fpasswd")
    assert response.status_code == 404
