# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Seed medical pdfs are gitignored generated artifacts, so they aren't in the
# source checkout. Generate them once at build time — no startup cost, no
# runtime write to /tmp on every cold start.
RUN /opt/venv/bin/python -m src.scripts.generate_medical_pdfs

FROM python:${PYTHON_VERSION}-slim AS runtime

# tini forwards SIGTERM to uvicorn so in-flight requests drain on scale-down.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0

WORKDIR /app
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --from=builder --chown=app:app /app/src ./src

# Owned by app so a mounted volume (or Cloud Run /tmp) is writable for sqlite + chroma.
RUN mkdir -p /data && chown app:app /data

USER app
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn src.main:app --host ${HOST} --port ${PORT}"]
