"""Temporary diagnostic endpoint for investigating why traces aren't flowing in prod.

Remove after the Langfuse/Cloud-Trace silence is resolved.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from opentelemetry import trace

router = APIRouter(prefix="/api/v1", tags=["diag"])

# Unprivileged token — intent is to keep this endpoint from being indexed/scraped,
# not to protect real secrets. Whole file is removed once the investigation ends.
_DIAG_TOKEN = "diag-98f3a2b1"


def _provider_info(p: object) -> dict[str, Any]:
    return {
        "id": id(p),
        "class": f"{type(p).__module__}.{type(p).__name__}",
    }


@router.get("/_trace_diag")
async def trace_diag(token: str = Query(...)) -> dict[str, Any]:
    if token != _DIAG_TOKEN:
        raise HTTPException(status_code=404)

    result: dict[str, Any] = {}

    global_provider = trace.get_tracer_provider()
    result["global_provider"] = _provider_info(global_provider)

    try:
        from langfuse import get_client

        client = get_client()
        lf_tracer = getattr(client, "_otel_tracer", None)
        result["langfuse_tracer_class"] = (
            f"{type(lf_tracer).__module__}.{type(lf_tracer).__name__}"
            if lf_tracer is not None
            else None
        )
        result["langfuse_tracer_is_noop"] = (
            "NoOp" in type(lf_tracer).__name__ if lf_tracer else None
        )

        resources = getattr(client, "_resources", None)
        if resources is not None:
            rm_provider = getattr(resources, "tracer_provider", None)
            result["langfuse_resource_provider"] = (
                _provider_info(rm_provider) if rm_provider is not None else None
            )
            result["langfuse_resource_provider_same_as_global"] = rm_provider is global_provider
    except Exception as e:
        result["langfuse_inspection_error"] = repr(e)

    manual_tracer = trace.get_tracer("trace_diag.manual")
    try:
        with manual_tracer.start_as_current_span("trace_diag.manual_span") as span:
            span.set_attribute("diag.kind", "manual")
        result["manual_span_created"] = True
    except Exception as e:
        result["manual_span_error"] = repr(e)

    try:
        from langfuse import get_client

        client = get_client()
        obs = client.start_observation(name="trace_diag.langfuse_span", as_type="span")
        obs.end()
        result["langfuse_span_created"] = True
        result["langfuse_span_trace_id"] = getattr(client, "last_trace_id", None)
    except Exception as e:
        result["langfuse_span_error"] = repr(e)

    try:
        started = time.perf_counter()
        if hasattr(global_provider, "force_flush"):
            flushed = global_provider.force_flush(timeout_millis=5000)
            result["global_force_flush_returned"] = flushed
            result["global_force_flush_ms"] = round((time.perf_counter() - started) * 1000)
        else:
            result["global_force_flush"] = "not available on provider"
    except Exception as e:
        result["global_force_flush_error"] = repr(e)

    try:
        started = time.perf_counter()
        from langfuse import get_client

        client = get_client()
        if hasattr(client, "flush"):
            client.flush()
            result["langfuse_flush_ms"] = round((time.perf_counter() - started) * 1000)
        else:
            result["langfuse_flush"] = "not available on client"
    except Exception as e:
        result["langfuse_flush_error"] = repr(e)

    return result
