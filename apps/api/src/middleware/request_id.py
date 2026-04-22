"""Stamp every request with X-Request-ID and bind it to the structlog context."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.services.log import bind

HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get(HEADER) or uuid4().hex
        request.state.request_id = rid
        bind(request_id=rid)
        response = await call_next(request)
        response.headers[HEADER] = rid
        return response
