"""Tests for the /api/v1/personas endpoint."""

from fastapi.testclient import TestClient


def test_list_personas_returns_five(client: TestClient) -> None:
    response = client.get("/api/v1/personas")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    ids = {p["id"] for p in body}
    assert {
        "alice-kigali-clean",
        "jean-nyanza-controlled-htn",
        "marie-rubavu-diabetic",
        "emmanuel-gakenke-cardiac",
        "claudine-nyagatare-pregnant",
    } == ids
    for p in body:
        assert {"id", "name", "age", "district", "headline"} <= set(p)


def test_get_persona_returns_full_applicant(client: TestClient) -> None:
    response = client.get("/api/v1/personas/alice-kigali-clean")
    assert response.status_code == 200
    body = response.json()
    assert body["applicant_id"] == "alice-kigali-clean"
    assert body["demographics"]["first_name"] == "Alice"


def test_get_persona_404(client: TestClient) -> None:
    response = client.get("/api/v1/personas/does-not-exist")
    assert response.status_code == 404
