"""
Wallet Service (Data Layer)
----------------------------
Read-only wallet balance access across supported chains.

In this hackathon build, live RPC calls are stubbed with a realistic mock
so the pipeline is fully runnable without external RPC/API dependencies.
Swap `get_balances` for a real `viem`/`web3.py` call per chain when wiring
up live testnet/mainnet reads — the interface stays the same.
"""
from app.config import settings


MOCK_BALANCES = {
    settings.DEMO_WALLET_ADDRESS: {
        "ethereum": {"USDC": 500.0, "ETH": 0.12},
        "base": {"USDC": 1500.0, "ETH": 0.05},
        "arbitrum": {"USDC": 0.0, "ETH": 0.02},
    }
}


def get_balances(address: str) -> dict:
    """Returns balances per chain per asset. Falls back to a demo wallet
    if the address isn't recognized, so the UI is never empty during a demo.
    """
    return MOCK_BALANCES.get(address, MOCK_BALANCES[settings.DEMO_WALLET_ADDRESS])


def get_total_usd(address: str) -> float:
    balances = get_balances(address)
    total = 0.0
    # crude demo pricing — USDC=1, ETH=3200
    prices = {"USDC": 1.0, "ETH": 3200.0}
    for chain_balances in balances.values():
        for asset, amount in chain_balances.items():
            total += amount * prices.get(asset, 0)
    return round(total, 2)
