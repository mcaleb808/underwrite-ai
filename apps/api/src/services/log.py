"""Structured JSON logging via structlog. Auto-configured on import."""

from __future__ import annotations

import logging
import sys
import time
from typing import Any
from uuid import UUID

import structlog
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from src.config import settings
from src.services.cost import estimate_cost

_configured = False


def configure() -> None:
    global _configured
    if _configured:
        return

    level = logging.getLevelNamesMapping().get(settings.LOG_LEVEL.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    # Route stdlib logs (uvicorn, sqlalchemy) through the same renderer.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level, force=True)
    _configured = True


def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)


def bind(**kwargs: Any) -> None:
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind(*keys: str) -> None:
    structlog.contextvars.unbind_contextvars(*keys)


def clear() -> None:
    structlog.contextvars.clear_contextvars()


def bind_node(state: Any, name: str) -> None:
    bind(node=name, task_id=state.get("task_id"))


def _empty_usage() -> dict[str, float]:
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "calls": 0,
    }


class LLMObservability(BaseCallbackHandler):
    """LangChain callback that logs each LLM call and accumulates per-task usage."""

    def __init__(self) -> None:
        self._start: dict[str, float] = {}
        self._task_usage: dict[str, dict[str, float]] = {}
        self._lifetime_usage: dict[str, float] = _empty_usage()
        self._log = get_logger("llm")

    def reset_task(self, task_id: str) -> None:
        self._task_usage[task_id] = _empty_usage()

    def get_usage(self, task_id: str) -> dict[str, float]:
        return self._task_usage.get(task_id, _empty_usage())

    def get_lifetime_usage(self) -> dict[str, float]:
        return dict(self._lifetime_usage)

    def discard_task(self, task_id: str) -> None:
        self._task_usage.pop(task_id, None)

    def _record_usage(
        self,
        model: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> None:
        cost = estimate_cost(model, prompt_tokens, completion_tokens)
        for bucket in (self._task_bucket(), self._lifetime_usage):
            if bucket is None:
                continue
            bucket["prompt_tokens"] += prompt_tokens
            bucket["completion_tokens"] += completion_tokens
            bucket["total_tokens"] += total_tokens
            bucket["cost_usd"] = round(bucket["cost_usd"] + cost, 6)
            bucket["calls"] += 1

    def _task_bucket(self) -> dict[str, float] | None:
        task_id = structlog.contextvars.get_contextvars().get("task_id")
        if not task_id or task_id not in self._task_usage:
            return None
        return self._task_usage[task_id]

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._start[str(run_id)] = time.perf_counter()

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._start[str(run_id)] = time.perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._start.pop(str(run_id), None)
        latency_ms = round((time.perf_counter() - start) * 1000) if start else None
        output = response.llm_output or {}
        usage = output.get("token_usage") or {}
        model = output.get("model_name")
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        self._record_usage(model, prompt_tokens, completion_tokens, total_tokens)
        self._log.info(
            "llm_call",
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._start.pop(str(run_id), None)
        latency_ms = round((time.perf_counter() - start) * 1000) if start else None
        self._log.warning("llm_call_error", latency_ms=latency_ms, error=repr(error))


llm_observability = LLMObservability()
configure()


def llm_callbacks() -> list[BaseCallbackHandler]:
    """Callbacks every ChatOpenAI in a node should receive."""
    callbacks: list[BaseCallbackHandler] = [llm_observability]
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        from langfuse.langchain import CallbackHandler

        callbacks.append(CallbackHandler())
    return callbacks


__all__ = [
    "LLMObservability",
    "bind",
    "bind_node",
    "clear",
    "configure",
    "get_logger",
    "llm_callbacks",
    "llm_observability",
    "unbind",
]
