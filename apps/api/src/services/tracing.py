"""OpenTelemetry setup: FastAPI auto-spans + GCP Cloud Trace + Langfuse."""

from __future__ import annotations

import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.config import settings
from src.services.log import get_logger

log = get_logger(__name__)

_configured = False


def configure_tracing(app: FastAPI) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    provider = TracerProvider(resource=Resource.create({"service.name": "underwrite-api"}))
    trace.set_tracer_provider(provider)

    # K_SERVICE is set by Cloud Run; skip Cloud Trace export in local dev.
    if os.environ.get("K_SERVICE"):
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

        provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))  # type: ignore[no-untyped-call]
        log.info("tracing_gcp_enabled")

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        from langfuse import Langfuse

        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
            tracer_provider=provider,
        )
        log.info("tracing_langfuse_enabled", host=settings.LANGFUSE_HOST)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


def tracer() -> trace.Tracer:
    return trace.get_tracer("underwrite-api")
