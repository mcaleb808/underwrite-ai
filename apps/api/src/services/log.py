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


class LLMObservability(BaseCallbackHandler):
    """LangChain callback emitting one llm_call event per invocation."""

    def __init__(self) -> None:
        self._start: dict[str, float] = {}
        self._log = get_logger("llm")

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
        self._log.info(
            "llm_call",
            model=output.get("model_name"),
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._start.pop(str(run_id), None)
        latency_ms = round((time.perf_counter() - start) * 1000) if start else None
        self._log.warning("llm_call_error", latency_ms=latency_ms, error=repr(error))


llm_observability = LLMObservability()
configure()


__all__ = [
    "LLMObservability",
    "bind",
    "bind_node",
    "clear",
    "configure",
    "get_logger",
    "llm_observability",
    "unbind",
]
