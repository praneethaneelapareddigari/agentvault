"""
Wallet Service (Data Layer)
----------------------------
Read-only wallet balance access across supported chains.

Two modes, selected by EXECUTION_MODE:
  - "mock" (default): realistic hardcoded balances, zero setup required.
  - "real": live Base Sepolia RPC reads (native ETH + USDC ERC20 balance)
    via web3.py, with automatic fallback to mock if the RPC call fails for
    any reason — a flaky RPC should never break the demo.
"""
from app.config import settings
from app.services.chain import get_web3

MOCK_BALANCES = {
    settings.DEMO_WALLET_ADDRESS: {
        "ethereum": {"USDC": 500.0, "ETH": 0.12},
        "base": {"USDC": 1500.0, "ETH": 0.05},
        "arbitrum": {"USDC": 0.0, "ETH": 0.02},
    }
}

_ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]


def get_balances_onchain(address: str) -> dict | None:
    """Real Base Sepolia balance read. Returns None (not an exception) on
    any failure so callers can cleanly fall back to mock data."""
    w3 = get_web3()
    if not w3:
        return None
    try:
        checksum = w3.to_checksum_address(address)
        eth_balance = w3.eth.get_balance(checksum) / 1e18
        result = {"base": {"ETH": round(eth_balance, 6)}}

        if settings.USDC_ADDRESS:
            usdc = w3.eth.contract(
                address=w3.to_checksum_address(settings.USDC_ADDRESS), abi=_ERC20_BALANCE_ABI
            )
            raw = usdc.functions.balanceOf(checksum).call()
            result["base"]["USDC"] = round(raw / 1e6, 2)  # USDC has 6 decimals

        return result
    except Exception:
        return None


def get_balances(address: str) -> dict:
    """Returns balances per chain per asset. In real mode, tries a live
    Base Sepolia RPC read first; falls back to the demo mock wallet if
    real reads aren't configured, fail, or the address is unrecognized —
    so the UI is never empty during a demo."""
    if settings.EXECUTION_MODE == "real":
        onchain = get_balances_onchain(address)
        if onchain:
            return onchain
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
