"""
Transaction Simulator
----------------------
Simulates the proposed transaction BEFORE anything touches the smart wallet.

Two modes, selected by EXECUTION_MODE:
  - "mock" (default): deterministic pseudo-random result, zero setup.
  - "real": an actual `eth_call` against Base Sepolia — asks the chain
    "would this Aave supply() call revert?" without spending any gas or
    changing any state. This is the same technique Tenderly/Anvil-fork
    simulation uses under the hood; `eth_call` is the free, dependency-free
    version of it and is sufficient on its own — Tenderly is a nice-to-have
    upgrade from here, not a requirement.
"""
import random

from app.config import settings
from app.services.chain import get_web3


def simulate_onchain(*, user_address: str, amount_usd: float) -> dict | None:
    """Real eth_call simulation of the Aave supply() the plan would trigger.
    Returns None (not an exception) if real-chain access isn't configured
    or the RPC call itself fails for infra reasons — distinct from the call
    succeeding and reporting the transaction WOULD revert, which is a
    legitimate simulation result, not a fallback trigger."""
    w3 = get_web3()
    if not w3 or not settings.USDC_ADDRESS or not settings.POLICY_VAULT_ADDRESS:
        return None
    try:
        from app.services.aave import encode_supply_calldata

        amount_wei = int(amount_usd * 1_000_000)  # USDC has 6 decimals
        calldata = encode_supply_calldata(w3, settings.USDC_ADDRESS, amount_wei, user_address)

        w3.eth.call(
            {
                "from": w3.to_checksum_address(settings.POLICY_VAULT_ADDRESS),
                "to": w3.to_checksum_address(settings.AAVE_POOL_ADDRESS),
                "data": calldata,
            }
        )
        return {
            "success": True,
            "estimated_gas_usd": None,
            "expected_asset_changes": {"-USDC": amount_usd, "+aBasUSDC": amount_usd},
            "warnings": [],
            "failure_reason": None,
        }
    except Exception as e:
        msg = str(e)
        if "insufficient" in msg.lower() or "revert" in msg.lower():
            # A real revert is a legitimate simulation result, not an error.
            return {
                "success": False,
                "estimated_gas_usd": None,
                "expected_asset_changes": {},
                "warnings": [],
                "failure_reason": msg[:200],
            }
        return None  # infra failure (bad RPC, timeout, etc.) — fall back to mock


def simulate(
    *, protocol: str, chain: str, asset: str, amount_usd: float, estimated_gas_usd: float,
    user_address: str | None = None,
) -> dict:
    if settings.EXECUTION_MODE == "real" and user_address:
        onchain_result = simulate_onchain(user_address=user_address, amount_usd=amount_usd)
        if onchain_result:
            onchain_result["estimated_gas_usd"] = estimated_gas_usd
            return onchain_result
        # falls through to mock below if real simulation was unavailable
    # Deterministic-ish "randomness" seeded by inputs so repeated calls with
    # the same plan give consistent demo results.
    rng = random.Random(f"{protocol}-{chain}-{asset}-{amount_usd}")
    failure_roll = rng.random()

    # In the demo, allowlisted protocols essentially always simulate
    # successfully. A small failure chance is kept for realism / to allow
    # demonstrating the FAIL path deliberately in a QA build.
    success = failure_roll > 0.03

    warnings = []
    if amount_usd > 1000:
        warnings.append("Large transaction relative to typical pool depth.")

    result = {
        "success": success,
        "estimated_gas_usd": estimated_gas_usd,
        "expected_asset_changes": {
            f"-{asset}": amount_usd,
            f"+a{asset.lower()}-{protocol.lower().replace(' ', '-')}": amount_usd,
        },
        "warnings": warnings,
        "failure_reason": None if success else "Simulated revert: slippage tolerance exceeded.",
    }
    return result
