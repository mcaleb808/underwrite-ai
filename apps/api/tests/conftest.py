"""Test fixtures: fresh DB per test, stubbed orchestrator, TestClient with overrides."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.models import Base
from src.db.session import get_session
from src.main import app
from src.routes import applications as applications_route


@pytest.fixture
def tmp_db_url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def tmp_engine(tmp_db_url: str):
    engine = create_async_engine(tmp_db_url, future=True)

    async def _create_all() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_create_all())
    finally:
        loop.close()
    return engine


@pytest.fixture
def session_factory(tmp_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(tmp_engine, expire_on_commit=False)


@pytest.fixture
def stub_orchestrator(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Any, list[str]]]:
    """Capture run_task calls without actually running the graph."""
    calls: list[tuple[str, Any, list[str]]] = []

    async def fake(task_id: str, applicant: Any, doc_paths: list[str]) -> None:
        calls.append((task_id, applicant, doc_paths))

    monkeypatch.setattr(applications_route, "run_task", fake)
    return calls


@pytest.fixture
def client(
    session_factory: async_sessionmaker[AsyncSession],
    stub_orchestrator: list,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setattr("src.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))

    async def override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
