"""Unit tests for the seed-on-startup logic - no chromadb or openai calls."""

from pathlib import Path

import pytest

from src.rag import ingest as ingest_mod


class _FakeCollection:
    def __init__(self, count: int) -> None:
        self._count = count

    def count(self) -> int:
        return self._count


def test_ensure_seeded_skips_when_collection_has_docs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(ingest_mod, "_collection", lambda _dir: _FakeCollection(15))
    called: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        ingest_mod, "ingest", lambda md, persist: called.append((Path(md), str(persist))) or 0
    )

    added = ingest_mod.ensure_seeded(tmp_path / "guidelines.md", str(tmp_path / "chroma"))

    assert added == 0
    assert called == []


def test_ensure_seeded_ingests_when_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ingest_mod, "_collection", lambda _dir: _FakeCollection(0))
    monkeypatch.setattr(ingest_mod, "ingest", lambda _md, _dir: 15)

    added = ingest_mod.ensure_seeded(tmp_path / "guidelines.md", str(tmp_path / "chroma"))

    assert added == 15
