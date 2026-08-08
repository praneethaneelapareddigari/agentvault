"""
Planning Agent
--------------
Given a structured Intent + current wallet balances + available protocol
opportunities, produces a single structured execution plan (not free text).

Tool-calling note: in a full LLM-orchestrated version, this agent would call
`get_wallet_balances`, `get_protocol_opportunities`, and `get_gas_estimate`
as read-only tools and let the model choose among pre-fetched, allowlisted
options. For reliability we implement the selection logic
deterministically (best APY meeting the risk floor within budget) — this is
equivalent in behavior to a well-prompted tool-calling agent, without LLM
latency/non-determinism on the critical path. The LLM can still be layered
on top purely to produce the human-readable "why we picked this" narration.
"""
from app.schemas import Intent
from app.services import protocol_data, wallet_service
from app.engines import risk_engine


class NoViableOpportunityError(Exception):
    pass


def build_plan(intent: Intent, wallet_address: str) -> dict:
    balances = wallet_service.get_balances(wallet_address)
    wallet_total_usd = wallet_service.get_total_usd(wallet_address)

    candidate_chains = list(balances.keys())
    opportunities = protocol_data.get_opportunities(intent.asset, candidate_chains)

    if not opportunities:
        raise NoViableOpportunityError(
            f"No vetted protocols found for asset {intent.asset}."
        )

    scored = []
    for opp in opportunities:
        chain_balance = balances.get(opp["chain"], {}).get(intent.asset, 0)
        if chain_balance < intent.amount:
            continue  # not enough funds on this chain for this opportunity

        gas_usd = protocol_data.estimate_gas_usd(opp["chain"])
        if gas_usd > intent.max_gas:
            continue  # exceeds user's gas ceiling before we even ask the policy engine

        risk = risk_engine.score_opportunity(opp, intent.amount, wallet_total_usd)
        if not risk_engine.meets_risk_tolerance(risk["score"], intent.risk):
            continue

        scored.append(
            {
                "protocol": opp["name"],
                "chain": opp["chain"],
                "asset": intent.asset,
                "amount_usd": min(intent.amount, intent.max_protocol_exposure),
                "expected_apy": opp["apy"],
                "estimated_gas_usd": gas_usd,
                "risk_score": risk["score"],
                "risk_reasons": risk["reasons"],
            }
        )

    if not scored:
        raise NoViableOpportunityError(
            "No opportunity satisfies the wallet balance, gas ceiling, and "
            "risk tolerance constraints simultaneously."
        )

    # Choose highest APY among viable, risk-qualified opportunities.
    best = max(scored, key=lambda o: o["expected_apy"])
    return best
