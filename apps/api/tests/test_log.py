"""Smoke tests for the structlog setup and the LLM observability callback."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
import structlog
from langchain_core.outputs import LLMResult

from src.services import log as logmod


@pytest.fixture(autouse=True)
def _reset_contextvars():
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


def _json_lines(stdout: str) -> list[dict]:
    out = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def test_configure_is_idempotent() -> None:
    logmod.configure()
    logmod.configure()
    logger = logmod.get_logger("test")
    logger.info("hello")


def test_bind_unbind_roundtrip() -> None:
    logmod.bind(task_id="t-123", node="critic")
    ctx = structlog.contextvars.get_contextvars()
    assert ctx == {"task_id": "t-123", "node": "critic"}
    logmod.unbind("node")
    ctx = structlog.contextvars.get_contextvars()
    assert ctx == {"task_id": "t-123"}
    logmod.clear()
    assert structlog.contextvars.get_contextvars() == {}


def test_bind_node_pulls_task_id_from_state() -> None:
    logmod.bind_node({"task_id": "t-9", "other": "ignored"}, "doc_parser")
    ctx = structlog.contextvars.get_contextvars()
    assert ctx == {"task_id": "t-9", "node": "doc_parser"}


def test_get_logger_emits_json_with_context(capsys: pytest.CaptureFixture[str]) -> None:
    logmod.bind(task_id="t-abc")
    logger = logmod.get_logger("structlog_smoke")
    logger.info("event_one", k=1)

    payloads = _json_lines(capsys.readouterr().out)
    matches = [p for p in payloads if p.get("event") == "event_one"]
    assert matches, f"no event_one payload found: {payloads}"
    assert matches[0]["task_id"] == "t-abc"
    assert matches[0]["k"] == 1


def test_llm_observability_emits_call_event(capsys: pytest.CaptureFixture[str]) -> None:
    logmod.bind(task_id="t-xyz", node="decision_draft")
    cb = logmod.LLMObservability()
    rid = uuid4()

    cb.on_llm_start({}, [""], run_id=rid)
    response = LLMResult(
        generations=[[]],
        llm_output={
            "model_name": "openai/gpt-4o-mini",
            "token_usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "total_tokens": 60,
            },
        },
    )
    cb.on_llm_end(response, run_id=rid)

    payloads = _json_lines(capsys.readouterr().out)
    matches = [p for p in payloads if p.get("event") == "llm_call"]
    assert matches, f"no llm_call payload found: {payloads}"
    payload = matches[-1]
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["prompt_tokens"] == 50
    assert payload["completion_tokens"] == 10
    assert payload["total_tokens"] == 60
    assert payload["task_id"] == "t-xyz"
    assert payload["node"] == "decision_draft"
    assert isinstance(payload["latency_ms"], int)
    assert payload["latency_ms"] >= 0


def test_llm_observability_handles_missing_usage(capsys: pytest.CaptureFixture[str]) -> None:
    cb = logmod.LLMObservability()
    rid = uuid4()
    cb.on_llm_start({}, [""], run_id=rid)
    cb.on_llm_end(LLMResult(generations=[[]], llm_output=None), run_id=rid)

    payloads = _json_lines(capsys.readouterr().out)
    matches = [p for p in payloads if p.get("event") == "llm_call"]
    assert matches
    assert matches[-1]["model"] is None
    assert matches[-1]["total_tokens"] == 0


def test_llm_observability_logs_errors(capsys: pytest.CaptureFixture[str]) -> None:
    cb = logmod.LLMObservability()
    rid = uuid4()
    cb.on_llm_start({}, [""], run_id=rid)
    cb.on_llm_error(RuntimeError("boom"), run_id=rid)

    payloads = _json_lines(capsys.readouterr().out)
    matches = [p for p in payloads if p.get("event") == "llm_call_error"]
    assert matches
    assert "boom" in matches[-1]["error"]


def _llm_response(model: str, prompt: int, completion: int) -> LLMResult:
    return LLMResult(
        generations=[[]],
        llm_output={
            "model_name": model,
            "token_usage": {
                "prompt_tokens": prompt,
                "completion_tokens": completion,
                "total_tokens": prompt + completion,
            },
        },
    )


def test_usage_accumulates_per_task() -> None:
    cb = logmod.LLMObservability()
    cb.reset_task("t-1")
    logmod.bind(task_id="t-1")

    rid1 = uuid4()
    cb.on_llm_start({}, [""], run_id=rid1)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 100, 50), run_id=rid1)

    rid2 = uuid4()
    cb.on_llm_start({}, [""], run_id=rid2)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 200, 100), run_id=rid2)

    usage = cb.get_usage("t-1")
    assert usage["prompt_tokens"] == 300
    assert usage["completion_tokens"] == 150
    assert usage["total_tokens"] == 450
    assert usage["calls"] == 2
    assert usage["cost_usd"] > 0


def test_usage_isolated_between_tasks() -> None:
    cb = logmod.LLMObservability()
    cb.reset_task("a")
    cb.reset_task("b")

    logmod.bind(task_id="a")
    rid_a = uuid4()
    cb.on_llm_start({}, [""], run_id=rid_a)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 100, 50), run_id=rid_a)

    logmod.bind(task_id="b")
    rid_b = uuid4()
    cb.on_llm_start({}, [""], run_id=rid_b)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 1, 1), run_id=rid_b)

    assert cb.get_usage("a")["prompt_tokens"] == 100
    assert cb.get_usage("b")["prompt_tokens"] == 1


def test_usage_ignored_when_task_not_reset() -> None:
    cb = logmod.LLMObservability()
    logmod.bind(task_id="not-tracked")
    rid = uuid4()
    cb.on_llm_start({}, [""], run_id=rid)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 100, 50), run_id=rid)

    # discard returns empty since we never reset
    usage = cb.get_usage("not-tracked")
    assert usage["total_tokens"] == 0
    assert usage["calls"] == 0


def test_discard_task_removes_state() -> None:
    cb = logmod.LLMObservability()
    cb.reset_task("t")
    logmod.bind(task_id="t")
    rid = uuid4()
    cb.on_llm_start({}, [""], run_id=rid)
    cb.on_llm_end(_llm_response("openai/gpt-4o-mini", 10, 5), run_id=rid)
    assert cb.get_usage("t")["calls"] == 1
    cb.discard_task("t")
    assert cb.get_usage("t")["calls"] == 0
