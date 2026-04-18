"""Tests for the /api/v1/districts endpoint."""

from fastapi.testclient import TestClient


def test_list_districts_returns_thirty_rows(client: TestClient) -> None:
    response = client.get("/api/v1/districts")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 30


def test_each_district_has_name_and_province(client: TestClient) -> None:
    body = client.get("/api/v1/districts").json()
    for row in body:
        assert set(row.keys()) == {"name", "province"}
        assert row["name"]
        assert row["province"]


def test_districts_cover_five_provinces(client: TestClient) -> None:
    body = client.get("/api/v1/districts").json()
    provinces = {row["province"] for row in body}
    assert provinces == {"Kigali", "Southern", "Western", "Northern", "Eastern"}
