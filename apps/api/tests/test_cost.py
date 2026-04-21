from src.services.cost import MODEL_PRICING, estimate_cost


def test_known_model_uses_pricing_table() -> None:
    cost = estimate_cost("openai/gpt-4o-mini", prompt_tokens=10_000, completion_tokens=2_000)
    expected = (
        10_000 * MODEL_PRICING["openai/gpt-4o-mini"]["input"] / 1_000_000
        + 2_000 * MODEL_PRICING["openai/gpt-4o-mini"]["output"] / 1_000_000
    )
    assert cost == round(expected, 6)


def test_unknown_model_returns_zero() -> None:
    assert estimate_cost("unknown/model", 1000, 1000) == 0.0


def test_missing_model_returns_zero() -> None:
    assert estimate_cost(None, 1000, 1000) == 0.0
