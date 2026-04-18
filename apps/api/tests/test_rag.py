"""RAG retrieval regression tests.

These tests verify that the top-1 result for each query matches
the expected rule_id. They require a seeded Chroma store and an
OpenAI API key for embeddings — marked slow so CI skips them.
"""

import pytest

from src.config import settings
from src.rag.retriever import retrieve

pytestmark = pytest.mark.slow


EXPECTED_TOP_HITS = [
    ("hypertension controlled blood pressure", "UW-030"),
    ("diabetes HbA1c insulin", "UW-040"),
    ("HIV ART adherence viral load", "UW-050"),
    ("tuberculosis treatment cleared", "UW-060"),
    ("pregnancy gestational diabetes", "UW-100"),
    ("ubudehe equity socio-economic bias", "UW-090"),
    ("BMI obesity overweight classification", "UW-020"),
    ("risk score verdict accept decline", "UW-130"),
    ("occupation mining motorcycle hazard", "UW-080"),
    ("malaria district endemic loading", "UW-070"),
    ("tobacco smoking alcohol lifestyle", "UW-110"),
    ("fairness critic checks mandatory", "UW-140"),
]


@pytest.mark.parametrize("query, expected_rule", EXPECTED_TOP_HITS)
def test_top_hit_matches_expected_rule(query: str, expected_rule: str) -> None:
    results = retrieve(query, settings.CHROMA_DIR, k=1)
    assert len(results) == 1
    assert results[0].rule_id == expected_rule, (
        f"query '{query}' returned {results[0].rule_id}, expected {expected_rule}"
    )
