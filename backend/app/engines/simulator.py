"""
Transaction Simulator
----------------------
Simulates the proposed transaction BEFORE anything touches the smart wallet.

Hackathon fallback strategy (see build plan risk #3): a real deployment would
call Tenderly's simulation API or run against a local Anvil fork via
`eth_call`. Both require live RPC/API access this sandboxed environment
doesn't have, so this module implements the same interface with a
deterministic mock — swap `simulate` internals for a real fork/Tenderly call
without touching any caller.
"""
import random


def simulate(
    *, protocol: str, chain: str, asset: str, amount_usd: float, estimated_gas_usd: float
) -> dict:
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
