"""Test fixtures: fresh DB per test, stubbed orchestrator, TestClient with overrides."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.models import Base
from src.db.session import get_session, get_session_factory
from src.main import app
from src.routes import applications as applications_route
from src.services.email import EmailMessage, SendResult, get_email_provider

_DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"


@pytest.fixture(scope="session", autouse=True)
def _ensure_seed_pdfs() -> None:
    """Make sure every persona's referenced medical PDFs exist on disk.

    The real PDFs are gitignored generated artifacts. CI doesn't have them,
    and several routes (notably create_application -> _copy_seed_docs) read
    them from src/data/medical_pdfs/. Write a tiny PDF stub for any missing
    file so tests don't depend on dev-machine state.
    """
    pdfs_dir = _DATA_DIR / "medical_pdfs"
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    for persona_path in (_DATA_DIR / "applicants").glob("*.json"):
        persona = json.loads(persona_path.read_text())
        for rel in persona.get("medical_docs", []):
            target = _DATA_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                # Minimal valid PDF header - pypdf can open it as 0-page doc
                target.write_bytes(b"%PDF-1.4\n%%EOF\n")


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


class FakeEmailProvider:
    name = "fake"

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, msg: EmailMessage) -> SendResult:
        self.sent.append(msg)
        return SendResult(status="sent", provider_message_id=f"fake-{len(self.sent)}")


@pytest.fixture
def fake_email() -> FakeEmailProvider:
    return FakeEmailProvider()


@pytest.fixture
def client(
    session_factory: async_sessionmaker[AsyncSession],
    stub_orchestrator: list,
    fake_email: FakeEmailProvider,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setattr("src.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))

    # Stub the email composer so route tests don't burn real LLM credits.
    from src.services.email import composer as composer_mod

    def _stub_compose(reference, first_name, decision):
        return composer_mod.ComposedEmail(
            subject=f"UnderwriteAI - Reference {reference}",
            body=(
                f"Dear {first_name},\n\n"
                f"This is a deterministic test-stub email body for {reference}.\n\n"
                f"-- UnderwriteAI"
            ),
        )

    monkeypatch.setattr(composer_mod, "compose", _stub_compose)

    async def override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_email_provider] = lambda: fake_email
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
