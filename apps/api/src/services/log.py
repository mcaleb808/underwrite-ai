"""Structured JSON logging via structlog.

All application logs are written to stdout as one JSON line per event.
Cloud Run (and any other container runtime) auto-forwards stdout to its
logging backend, where logs are queryable by ``task_id``, ``node``, and
any other context bound via :func:`bind`.

The module is auto-configured on first import; ``configure()`` is
idempotent so re-imports and test runs don't double-register processors.

A :class:`LLMObservability` callback is exported as ``llm_observability``
and should be attached to every ``ChatOpenAI`` (or other LangChain LLM)
constructed inside a node — it emits one ``llm_call`` event per
invocation with model, latency, and token usage.
"""

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
    """Configure structlog. Idempotent — safe to call multiple times."""
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

    # Route the stdlib logging tree (uvicorn, sqlalchemy, etc.) through the
    # same JSON renderer so every line in stdout is parseable by Cloud Logging.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level, force=True)

    _configured = True


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger bound to ``name`` (typically ``__name__``)."""
    return structlog.get_logger(name)


def bind(**kwargs: Any) -> None:
    """Bind key/value pairs to the current async context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind(*keys: str) -> None:
    """Remove keys from the current async context."""
    structlog.contextvars.unbind_contextvars(*keys)


def clear() -> None:
    """Drop all bound context vars."""
    structlog.contextvars.clear_contextvars()


class LLMObservability(BaseCallbackHandler):
    """LangChain callback that emits structlog events for each LLM call.

    Records latency and token usage. Reads ``task_id`` and ``node`` from the
    structlog context (bound by the orchestrator and node ``run`` functions),
    so the emitted event is automatically correlated with its caller.
    """

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
        usage = output.get("token_usage") or output.get("usage") or {}
        self._log.info(
            "llm_call",
            model=output.get("model_name") or output.get("model"),
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens") or usage.get("input_tokens"),
            completion_tokens=usage.get("completion_tokens") or usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._start.pop(str(run_id), None)
        latency_ms = round((time.perf_counter() - start) * 1000) if start else None
        self._log.warning("llm_call_error", latency_ms=latency_ms, error=repr(error))


# Singleton callback shared across every LLM constructed in the app.
llm_observability = LLMObservability()


# Auto-configure on import so any module that imports get_logger gets
# structured output without further setup.
configure()


__all__ = [
    "LLMObservability",
    "bind",
    "clear",
    "configure",
    "get_logger",
    "llm_observability",
    "unbind",
]
