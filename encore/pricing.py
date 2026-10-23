"""Token rate card and cost math, so the report can quote real dollars.

Prices are USD per 1M tokens for the course model (OpenAI pricing, Oct 2026).
"""

RATE_CARD = {
    "gpt-6-luna": {"input": 0.10, "cached_input": 0.01, "output": 0.50},
}
DEFAULT_MODEL = "gpt-6-luna"


def cost_usd(model: str, input_tokens: int, output_tokens: int,
             cached_tokens: int = 0) -> float:
    r = RATE_CARD.get(model, RATE_CARD[DEFAULT_MODEL])
    cached = max(0, min(cached_tokens, input_tokens))
    fresh = max(0, input_tokens - cached)
    return (
        fresh / 1_000_000 * r["input"]
        + cached / 1_000_000 * r["cached_input"]
        + max(0, output_tokens) / 1_000_000 * r["output"]
    )
