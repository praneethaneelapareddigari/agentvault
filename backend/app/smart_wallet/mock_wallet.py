"""
Smart Wallet (execution layer)
--------------------------------
This is the ONLY module allowed to "execute" anything, and it only ever
executes a plan that has already passed Policy Engine + Simulator + explicit
user approval — enforced by the router, not by this module alone (defense
in depth: even if this function were called directly, it still refuses to
run without a passed policy_status/simulation_status, see `require_authorized`).

Real implementation options (see architecture doc):
  1. Safe (Gnosis Safe) + custom policy module        <- recommended
  2. ERC-4337 smart account                           <- higher effort/risk
  3. Custom PolicyVault.sol relayer-restricted contract <- fallback, see /contracts

This module implements the same interface as option 3 (a backend relayer
calling a restricted `executeIfApproved` function) but mocks the actual
chain call so the backend runs without live RPC access. Swap `_send_tx`
for a real web3/viem call to `contracts/PolicyVault.sol` when deploying.
"""
import hashlib
import time


class UnauthorizedExecutionError(Exception):
    pass


def require_authorized(plan) -> None:
    if plan.policy_status != "PASS":
        raise UnauthorizedExecutionError("Plan has not passed the Policy Engine.")
    if plan.simulation_status != "PASS":
        raise UnauthorizedExecutionError("Plan has not passed the Transaction Simulator.")


def _send_tx(plan) -> dict:
    """Mocked chain call. Real version: sign+submit a UserOp / Safe tx /
    PolicyVault.executeIfApproved() call via viem/ethers, then poll for
    the receipt."""
    payload = f"{plan.id}-{plan.protocol}-{plan.chain}-{plan.amount_usd}-{time.time()}"
    tx_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()[:64]
    return {
        "tx_hash": tx_hash,
        "status": "confirmed",
        "block_number": 10_000_000 + int(time.time()) % 100000,
        "explorer_url": None,  # mock execution never touches a real chain
    }


def execute(plan) -> dict:
    require_authorized(plan)
    return _send_tx(plan)
