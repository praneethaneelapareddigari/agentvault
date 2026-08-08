"""
Protocol Data Service
----------------------
Hardcoded, vetted allowlist of protocols for the MVP demo. Deliberately NOT
a general "any protocol" integration — see Risk Engine notes for why.

Live version (future extension): pull from protocol APIs / subgraphs / DefiLlama
per chain, still filtered through the same allowlist + risk model.
"""

PROTOCOLS = [
    {
        "name": "Aave v3",
        "chain": "base",
        "asset": "USDC",
        "apy": 4.8,
        "base_risk_score": 92,
        "category": "lending",
    },
    {
        "name": "Compound v3",
        "chain": "base",
        "asset": "USDC",
        "apy": 4.2,
        "base_risk_score": 90,
        "category": "lending",
    },
    {
        "name": "Moonwell",
        "chain": "base",
        "asset": "USDC",
        "apy": 6.1,
        "base_risk_score": 78,
        "category": "lending",
    },
    {
        "name": "Aave v3",
        "chain": "ethereum",
        "asset": "USDC",
        "apy": 3.9,
        "base_risk_score": 93,
        "category": "lending",
    },
    {
        "name": "Aave v3",
        "chain": "arbitrum",
        "asset": "USDC",
        "apy": 4.5,
        "base_risk_score": 91,
        "category": "lending",
    },
]

ALLOWED_PROTOCOL_NAMES = {p["name"] for p in PROTOCOLS}


def get_opportunities(asset: str, chains: list[str] | None = None) -> list[dict]:
    results = [p for p in PROTOCOLS if p["asset"] == asset]
    if chains:
        results = [p for p in results if p["chain"] in chains]
    return sorted(results, key=lambda p: p["apy"], reverse=True)


def estimate_gas_usd(chain: str) -> float:
    # Rough, deliberately conservative demo gas estimates per chain.
    return {"base": 0.15, "arbitrum": 0.35, "ethereum": 4.20}.get(chain, 1.0)
