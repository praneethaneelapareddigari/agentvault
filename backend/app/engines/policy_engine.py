"""
Policy Engine
-------------
THE core security boundary of AgentVault.

Hard rule enforced by construction: nothing in this module ever calls or is
influenced by an LLM. It receives a fully-formed execution plan (produced by
the Planning Agent) and a user's Policy row, and deterministically returns
PASS or FAIL with explicit reasons. The AI can propose; only this module
(plus explicit user approval) can authorize.

If you take one file away from this codebase as "the pitch", it's this one —
keep it small, keep it dependency-free, keep it unit-testable in isolation.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PolicyCheckResult:
    passed: bool
    reasons: list[str]
    requires_manual_approval: bool


def evaluate_plan(
    *,
    amount_usd: float,
    chain: str,
    protocol: str,
    estimated_gas_usd: float,
    risk_score: int,
    policy,  # app.models.Policy instance (or any object with matching attrs)
) -> PolicyCheckResult:
    reasons: list[str] = []
    passed = True

    if amount_usd > float(policy.max_tx_usd):
        passed = False
        reasons.append(
            f"Transaction amount ${amount_usd:.2f} exceeds max_tx_usd "
            f"limit of ${float(policy.max_tx_usd):.2f}."
        )

    if amount_usd > float(policy.max_protocol_exposure_usd):
        passed = False
        reasons.append(
            f"Amount ${amount_usd:.2f} exceeds max single-protocol exposure "
            f"limit of ${float(policy.max_protocol_exposure_usd):.2f}."
        )

    if estimated_gas_usd > float(policy.max_gas_usd):
        passed = False
        reasons.append(
            f"Estimated gas ${estimated_gas_usd:.2f} exceeds max_gas_usd "
            f"limit of ${float(policy.max_gas_usd):.2f}."
        )

    allowed_chains = policy.allowed_chains or []
    if allowed_chains and chain not in allowed_chains:
        passed = False
        reasons.append(f"Chain '{chain}' is not in the user's allowed_chains list.")

    allowed_protocols = policy.allowed_protocols or []
    if allowed_protocols and protocol not in allowed_protocols:
        passed = False
        reasons.append(f"Protocol '{protocol}' is not in the user's allowed_protocols list.")

    if risk_score < int(policy.min_risk_score):
        passed = False
        reasons.append(
            f"Risk score {risk_score} is below the user's min_risk_score "
            f"threshold of {policy.min_risk_score}."
        )

    if not reasons:
        reasons.append("All policy checks passed.")

    requires_manual_approval = amount_usd >= float(policy.approval_threshold_usd)

    return PolicyCheckResult(
        passed=passed,
        reasons=reasons,
        requires_manual_approval=requires_manual_approval or True,
        # NOTE: in this MVP EVERY sensitive transaction requires explicit
        # user approval regardless of threshold (see SECURITY.md /
        # section 10 of the product spec: "NEVER allow silent high-value
        # transactions"). approval_threshold_usd is kept for future use
        # (e.g. distinguishing one-click vs. two-step confirmation UX)
        # but does not currently allow bypassing approval entirely.
    )
