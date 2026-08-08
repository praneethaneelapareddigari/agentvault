"""
Intent Agent
------------
Converts a free-text user prompt into a strictly-typed Intent object.

Design note (security-relevant): this agent NEVER produces anything that is
executed directly. Its only output is a validated Pydantic `Intent` object
consumed by the Planning Agent. If Anthropic API access is configured, we use
Claude with structured/JSON output; otherwise we fall back to a deterministic
rule-based parser so the whole pipeline still runs without any API key.
"""
import json
import re

from app.config import settings
from app.schemas import Intent

SYSTEM_PROMPT = """You convert a user's natural-language on-chain request into JSON matching this exact schema:
{
  "goal": "maximize_yield",
  "asset": "USDC",
  "amount": 500,
  "risk": "low" | "medium" | "high",
  "max_gas": 5,
  "max_protocol_exposure": 500
}
Respond with ONLY the JSON object, no prose, no markdown fences."""


def _parse_with_llm(prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    text = text.strip("`")
    if text.startswith("json"):
        text = text[4:].strip()
    return json.loads(text)


def _parse_with_rules(prompt: str) -> dict:
    """Deterministic fallback parser — no external API required.

    Handles prompts of the shape used throughout the AgentVault spec, e.g.:
    "Find a low-risk yield opportunity for $500 USDC. Don't spend more than
    $5 in gas and never put more than $500 into one protocol."
    """
    p = prompt.lower()

    amount_match = re.search(r"\$?(\d+(?:\.\d+)?)\s*(usdc|usdt|dai|eth)?", p)
    amount = float(amount_match.group(1)) if amount_match else 500.0

    asset_match = re.search(r"\b(usdc|usdt|dai|eth|weth)\b", p)
    asset = asset_match.group(1).upper() if asset_match else "USDC"

    if "high-risk" in p or "high risk" in p:
        risk = "high"
    elif "medium-risk" in p or "medium risk" in p:
        risk = "medium"
    else:
        risk = "low"  # sensible conservative default

    gas_match = re.search(r"(?:gas|fees?).{0,15}?\$?(\d+(?:\.\d+)?)", p)
    max_gas = float(gas_match.group(1)) if gas_match else 5.0

    exposure_match = re.search(
        r"(?:one protocol|per protocol|single protocol).{0,15}?\$?(\d+(?:\.\d+)?)"
        r"|\$?(\d+(?:\.\d+)?).{0,25}?(?:one protocol|per protocol)",
        p,
    )
    if exposure_match:
        max_protocol_exposure = float(
            exposure_match.group(1) or exposure_match.group(2)
        )
    else:
        max_protocol_exposure = amount

    goal = "maximize_yield"

    return {
        "goal": goal,
        "asset": asset,
        "amount": amount,
        "risk": risk,
        "max_gas": max_gas,
        "max_protocol_exposure": max_protocol_exposure,
    }


def extract_intent(prompt: str) -> Intent:
    raw: dict
    if settings.ANTHROPIC_API_KEY:
        try:
            raw = _parse_with_llm(prompt)
        except Exception:
            # Never let an LLM/API hiccup break the pipeline — fall back.
            raw = _parse_with_rules(prompt)
    else:
        raw = _parse_with_rules(prompt)

    return Intent(**raw)
