"""
Risk Engine
-----------
Deterministic, non-LLM risk scoring. Intentionally simple and explainable:
a general contract-risk static analyzer is out of scope for this build,
so risk is derived from:

  1. A vetted protocol allowlist with pre-assigned base risk scores
     (audits/TVL/track record considered offline, not computed live).
  2. Transaction-size risk adjustment (larger relative size -> small penalty).
  3. Requested risk tolerance from the user's intent.

Anything NOT on the allowlist automatically scores 0 and is rejected
downstream by the Policy Engine — the agent cannot "talk its way" onto
an unvetted protocol.
"""
from app.services.protocol_data import ALLOWED_PROTOCOL_NAMES

RISK_TOLERANCE_FLOOR = {
    "low": 80,
    "medium": 60,
    "high": 40,
}


def score_opportunity(protocol: dict, amount_usd: float, wallet_total_usd: float) -> dict:
    if protocol["name"] not in ALLOWED_PROTOCOL_NAMES:
        return {
            "score": 0,
            "reasons": [f"Protocol '{protocol['name']}' is not on the vetted allowlist."],
        }

    score = protocol["base_risk_score"]
    reasons = [f"Base risk score for {protocol['name']}: {protocol['base_risk_score']}"]

    # Concentration penalty: putting a large % of the wallet into one tx
    if wallet_total_usd > 0:
        concentration = amount_usd / wallet_total_usd
        if concentration > 0.5:
            score -= 10
            reasons.append("Penalty: transaction is >50% of wallet holdings.")
        elif concentration > 0.25:
            score -= 5
            reasons.append("Penalty: transaction is >25% of wallet holdings.")

    score = max(0, min(100, score))
    return {"score": score, "reasons": reasons}


def meets_risk_tolerance(score: int, requested_risk: str) -> bool:
    floor = RISK_TOLERANCE_FLOOR.get(requested_risk, 80)
    return score >= floor
