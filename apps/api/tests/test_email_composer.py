"""Composer tests - no real LLM calls."""

import pytest

from src.schemas.decision import DecisionDraft
from src.services.email import composer as composer_mod


def _decision(verdict: str = "accept_with_conditions", loading: float = 25.0) -> DecisionDraft:
    return DecisionDraft(
        verdict=verdict,  # type: ignore[arg-type]
        premium_loading_pct=loading,
        conditions=[
            "Age-band loading of 15% applied for age 31-45 per UW-010",
            "BMI loading of 10% applied for overweight status per UW-020",
        ],
        reasoning="Risk score 26.2 maps to accept_with_conditions per UW-130.",
        citations=["UW-130", "UW-010", "UW-020"],
    )


class _FakeChain:
    """Mimics the with_structured_output().with_retry() chain shape."""

    def __init__(self, result: composer_mod.ComposedEmail | Exception) -> None:
        self._result = result
        self.calls: list[list] = []

    def with_retry(self, **_kwargs: object) -> "_FakeChain":
        return self

    def invoke(self, messages: list) -> composer_mod.ComposedEmail:
        self.calls.append(messages)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class _FakeLLM:
    def __init__(self, chain: _FakeChain) -> None:
        self._chain = chain

    def with_structured_output(self, _schema: type) -> _FakeChain:
        return self._chain


def test_compose_returns_llm_output_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = composer_mod.ComposedEmail(
        subject="UnderwriteAI - Approved (UW-2026-X)",
        body="Dear Alice,\n\nGreat news - your coverage is approved.\n\n-- UnderwriteAI",
    )
    chain = _FakeChain(expected)
    monkeypatch.setattr(composer_mod, "_llm", lambda: _FakeLLM(chain))

    result = composer_mod.compose("UW-2026-X", "Alice", _decision(verdict="accept", loading=0))

    assert result == expected
    assert chain.calls, "compose must call invoke once"


def test_compose_falls_back_when_llm_throws(monkeypatch: pytest.MonkeyPatch) -> None:
    chain = _FakeChain(RuntimeError("openrouter exploded"))
    monkeypatch.setattr(composer_mod, "_llm", lambda: _FakeLLM(chain))

    result = composer_mod.compose("UW-2026-Y", "Alice", _decision(verdict="decline"))

    assert "Alice" in result.body
    assert "UW-2026-Y" in result.body
    assert "Update on your application" in result.body
    # Fallback must not leak the verdict enum either.
    assert "decline" not in result.body.lower() or "decline" in result.subject.lower()


def test_user_prompt_does_not_include_reasoning_or_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = composer_mod.ComposedEmail(
        subject="X - Y (UW-X)",
        body="Dear Alice,\n\nThis is a sufficiently long stub body for tests.\n\n-- X",
    )
    chain = _FakeChain(expected)
    monkeypatch.setattr(composer_mod, "_llm", lambda: _FakeLLM(chain))

    composer_mod.compose("UW-2026-Z", "Alice", _decision())

    user_msg = chain.calls[0][1].content
    # The reasoning paragraph and the rule citation list are internal-only.
    assert "Risk score 26.2" not in user_msg
    assert "UW-130" not in user_msg
    # The raw loading percentage must never reach the LLM.
    assert "25.0" not in user_msg
    assert "premium_loading_pct" not in user_msg
    # The conditions list (which we DO want rewritten) is included.
    assert "Age-band loading" in user_msg


def test_user_prompt_signals_premium_adjustment_qualitatively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = composer_mod.ComposedEmail(
        subject="X - Y (R)",
        body="Dear Alice,\n\nThis is a sufficiently long stub body for tests.\n\n-- X",
    )
    chain = _FakeChain(expected)
    monkeypatch.setattr(composer_mod, "_llm", lambda: _FakeLLM(chain))

    composer_mod.compose("R", "Alice", _decision(verdict="accept_with_conditions", loading=25.0))
    msg_with_loading = chain.calls[-1][1].content

    composer_mod.compose("R", "Alice", _decision(verdict="accept", loading=0))
    msg_without_loading = chain.calls[-1][1].content

    assert "Premium adjustment applies: yes" in msg_with_loading
    assert "Premium adjustment applies: no" in msg_without_loading


def test_fallback_handles_unknown_verdict() -> None:
    result = composer_mod._fallback("UW-X", "Alice", "weird_new_verdict")
    assert "Alice" in result.body
    assert "UW-X" in result.body
    # Generic headline used when verdict is unknown.
    assert "Update on your application" in result.body
