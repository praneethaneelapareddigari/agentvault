from types import SimpleNamespace
from app.engines.policy_engine import evaluate_plan


def make_policy(**overrides):
    base = dict(
        max_tx_usd=500,
        max_protocol_exposure_usd=500,
        max_gas_usd=5,
        allowed_chains=["ethereum", "base", "arbitrum"],
        allowed_protocols=[],
        min_risk_score=80,
        approval_threshold_usd=250,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_passes_when_within_all_limits():
    policy = make_policy()
    result = evaluate_plan(
        amount_usd=500, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.15, risk_score=92, policy=policy,
    )
    assert result.passed is True


def test_fails_when_amount_exceeds_max_tx():
    policy = make_policy(max_tx_usd=100)
    result = evaluate_plan(
        amount_usd=500, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.15, risk_score=92, policy=policy,
    )
    assert result.passed is False
    assert any("max_tx_usd" in r for r in result.reasons)


def test_fails_when_gas_exceeds_limit():
    policy = make_policy(max_gas_usd=0.01)
    result = evaluate_plan(
        amount_usd=100, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.15, risk_score=92, policy=policy,
    )
    assert result.passed is False
    assert any("gas" in r.lower() for r in result.reasons)


def test_fails_when_chain_not_allowed():
    policy = make_policy(allowed_chains=["ethereum"])
    result = evaluate_plan(
        amount_usd=100, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.15, risk_score=92, policy=policy,
    )
    assert result.passed is False
    assert any("chain" in r.lower() for r in result.reasons)


def test_fails_when_risk_score_below_floor():
    policy = make_policy(min_risk_score=95)
    result = evaluate_plan(
        amount_usd=100, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.15, risk_score=92, policy=policy,
    )
    assert result.passed is False
    assert any("risk score" in r.lower() for r in result.reasons)


def test_every_transaction_requires_approval():
    policy = make_policy(approval_threshold_usd=1_000_000)
    result = evaluate_plan(
        amount_usd=1, chain="base", protocol="Aave v3",
        estimated_gas_usd=0.01, risk_score=92, policy=policy,
    )
    # Even a tiny transaction below the "threshold" still requires approval —
    # AgentVault never silently executes.
    assert result.requires_manual_approval is True
