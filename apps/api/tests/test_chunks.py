"""Unit tests for the markdown chunker — no API calls needed."""

from pathlib import Path

from src.rag.chunks import chunk_markdown

GUIDELINES_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "guidelines.md"


def test_chunks_all_rules_extracted() -> None:
    text = GUIDELINES_PATH.read_text()
    chunks = chunk_markdown(text)
    rule_ids = [c["rule_id"] for c in chunks]

    expected = [
        "UW-001",
        "UW-010",
        "UW-020",
        "UW-030",
        "UW-040",
        "UW-050",
        "UW-060",
        "UW-070",
        "UW-080",
        "UW-090",
        "UW-100",
        "UW-110",
        "UW-120",
        "UW-130",
        "UW-140",
    ]
    assert rule_ids == expected


def test_chunks_have_required_keys() -> None:
    text = GUIDELINES_PATH.read_text()
    chunks = chunk_markdown(text)

    for chunk in chunks:
        assert "rule_id" in chunk
        assert "section_title" in chunk
        assert "text" in chunk
        assert chunk["text"].startswith("## ")


def test_chunks_section_titles_not_empty() -> None:
    text = GUIDELINES_PATH.read_text()
    chunks = chunk_markdown(text)

    for chunk in chunks:
        assert len(chunk["section_title"]) > 0, f"{chunk['rule_id']} has empty title"
