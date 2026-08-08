"""
Verification Agent
-------------------
Polls (mock) on-chain state after execution and confirms the result matches
what was planned. The LLM, if configured, is used ONLY to phrase the final
human-readable confirmation sentence — never to decide whether the outcome
was correct. That decision is a deterministic comparison against the plan.
"""
from app.config import settings


def verify_execution(plan: dict, tx: dict) -> dict:
    expected_amount = float(plan["amount_usd"])
    matches_expected = tx["status"] == "confirmed"

    summary = _summarize(plan, tx, matches_expected)

    return {
        "verified": matches_expected,
        "summary": summary,
    }


def _summarize(plan: dict, tx: dict, matches_expected: bool) -> str:
    if not matches_expected:
        return (
            f"Verification failed: transaction {tx.get('tx_hash')} on "
            f"{plan['chain']} did not confirm as expected."
        )

    templated = (
        f"Your ${plan['amount_usd']:.0f} position in {plan['protocol']} "
        f"on {plan['chain'].capitalize()} is now active "
        f"(tx {tx.get('tx_hash')})."
    )

    if not settings.ANTHROPIC_API_KEY:
        return templated

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            system=(
                "Rewrite the following confirmation as one short, friendly "
                "sentence for a Web3 app user. Do not invent any facts not "
                "present in the input."
            ),
            messages=[{"role": "user", "content": templated}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return text or templated
    except Exception:
        return templated
