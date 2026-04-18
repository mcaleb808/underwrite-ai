"""Route tests for /api/v1/applications — no LLM calls (orchestrator stubbed)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

ALICE = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "data"
    / "applicants"
    / "alice-kigali-clean.json"
)


def _alice_form() -> dict[str, str]:
    return {"applicant": ALICE.read_text()}


def test_create_application_returns_202_and_task_id(
    client: TestClient, stub_orchestrator: list[tuple[str, Any, list[str]]]
) -> None:
    response = client.post("/api/v1/applications", data=_alice_form())
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["reference_number"].startswith("UW-")
    assert len(body["task_id"]) == 32
    assert body["status_url"].endswith(f"/api/v1/applications/{body['task_id']}")
    assert len(stub_orchestrator) == 1
    captured_task_id, captured_applicant, captured_paths = stub_orchestrator[0]
    assert captured_task_id == body["task_id"]
    assert captured_applicant.applicant_id == "alice-kigali-clean"
    # persona has a seed PDF -> copied into the upload dir for download
    assert len(captured_paths) == 1
    assert captured_paths[0].endswith("alice-kigali-clean.pdf")
    assert Path(captured_paths[0]).is_file()


def test_create_application_persists_uploaded_pdfs(
    client: TestClient,
    stub_orchestrator: list[tuple[str, Any, list[str]]],
    tmp_path: Path,
) -> None:
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
    response = client.post(
        "/api/v1/applications",
        data=_alice_form(),
        files=[("medical_docs", ("scan.pdf", fake_pdf, "application/pdf"))],
    )
    assert response.status_code == 202
    _, _, paths = stub_orchestrator[0]
    assert len(paths) == 1
    assert Path(paths[0]).read_bytes() == b"%PDF-1.4 fake"


def test_create_application_rejects_invalid_payload(client: TestClient) -> None:
    bad = json.dumps({"applicant_id": "bad", "demographics": {}})
    response = client.post("/api/v1/applications", data={"applicant": bad})
    assert response.status_code == 422


def test_get_application_404_for_unknown_task(client: TestClient) -> None:
    response = client.get("/api/v1/applications/does-not-exist")
    assert response.status_code == 404


def test_get_application_returns_status_after_post(
    client: TestClient, stub_orchestrator: list
) -> None:
    created = client.post("/api/v1/applications", data=_alice_form()).json()

    response = client.get(f"/api/v1/applications/{created['task_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == created["task_id"]
    assert body["reference_number"] == created["reference_number"]
    # orchestrator is stubbed, so status stays queued and decision is null
    assert body["status"] == "queued"
    assert body["decision"] is None
    assert body["risk_score"] is None


@pytest.mark.parametrize("missing_field", ["applicant"])
def test_create_application_missing_field(client: TestClient, missing_field: str) -> None:
    response = client.post("/api/v1/applications", data={})
    assert response.status_code == 422
