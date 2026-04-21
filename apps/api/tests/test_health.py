from fastapi.testclient import TestClient


def test_health_returns_subsystem_status(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"status", "db", "chroma", "llm_provider"}
    assert body["db"] == "ok"
    assert body["status"] in {"ok", "degraded"}
    assert body["chroma"] in {"ok", "empty", "error"}
    assert body["llm_provider"] in {"configured", "missing"}


def test_metrics_returns_counters(client: TestClient) -> None:
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "decisions_total",
        "decisions_failed",
        "tasks_total",
        "total_tokens_since_start",
        "total_cost_usd_since_start",
        "llm_calls_since_start",
    }
    for key in (
        "decisions_total",
        "decisions_failed",
        "tasks_total",
        "total_tokens_since_start",
        "llm_calls_since_start",
    ):
        assert isinstance(body[key], int)
        assert body[key] >= 0
    assert isinstance(body["total_cost_usd_since_start"], int | float)
