"""LLM cost estimation. Prices are USD per 1M tokens, snapshot April 2026."""

from __future__ import annotations

# Snapshot of OpenRouter list prices. Update when models change.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "anthropic/claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def estimate_cost(model: str | None, prompt_tokens: int, completion_tokens: int) -> float:
    if not model:
        return 0.0
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    return round(
        prompt_tokens * pricing["input"] / 1_000_000
        + completion_tokens * pricing["output"] / 1_000_000,
        6,
    )
