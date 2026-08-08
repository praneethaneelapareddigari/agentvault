"""
Real Execution — Base Sepolia
-------------------------------
Sends an actual, signed transaction to Base Sepolia via the backend relayer
key, calling PolicyVault.executeIfApproved(), which the contract itself
then uses to call Aave V3 Pool.supply() on the user's behalf (see
contracts/PolicyVault.sol).

This is deliberately a separate module from smart_wallet/mock_wallet.py
rather than a flag inside it — the mock path must keep working with zero
configuration, and this path must never be reachable unless every required
setting is explicitly present (see is_configured()).
"""
from app.config import settings
from app.services.aave import encode_supply_calldata

POLICY_VAULT_ABI = [
    {
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "protocol", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "planId", "type": "bytes32"},
            {"name": "data", "type": "bytes"},
        ],
        "name": "executeIfApproved",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class RealExecutionUnavailable(Exception):
    pass


def is_configured() -> bool:
    return bool(
        settings.EXECUTION_MODE == "real"
        and settings.BASE_SEPOLIA_RPC_URL
        and settings.RELAYER_PRIVATE_KEY
        and settings.POLICY_VAULT_ADDRESS
        and settings.USDC_ADDRESS
    )


def execute(plan, user_wallet_address: str) -> dict:
    """Signs and broadcasts the real executeIfApproved() transaction, waits
    for the receipt, and returns a result shaped identically to
    mock_wallet.execute() plus an explorer_url — so callers never need to
    branch on which path ran."""
    if not is_configured():
        raise RealExecutionUnavailable(
            "Real execution requested but not fully configured — see backend/.env.example"
        )

    from web3 import Web3
    from eth_account import Account

    w3 = Web3(Web3.HTTPProvider(settings.BASE_SEPOLIA_RPC_URL, request_kwargs={"timeout": 20}))
    if not w3.is_connected():
        raise RealExecutionUnavailable("Could not connect to BASE_SEPOLIA_RPC_URL")

    account = Account.from_key(settings.RELAYER_PRIVATE_KEY)
    user = w3.to_checksum_address(user_wallet_address)
    amount_wei = int(float(plan.amount_usd) * 1_000_000)  # USDC has 6 decimals

    supply_calldata = encode_supply_calldata(w3, settings.USDC_ADDRESS, amount_wei, user)

    vault = w3.eth.contract(
        address=w3.to_checksum_address(settings.POLICY_VAULT_ADDRESS), abi=POLICY_VAULT_ABI
    )
    plan_id = Web3.keccak(text=str(plan.id))

    tx = vault.functions.executeIfApproved(
        user,
        w3.to_checksum_address(settings.AAVE_POOL_ADDRESS),
        w3.to_checksum_address(settings.USDC_ADDRESS),
        amount_wei,
        plan_id,
        supply_calldata,
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": settings.BASE_SEPOLIA_CHAIN_ID,
        }
    )

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    hash_hex = tx_hash.hex()
    if not hash_hex.startswith("0x"):
        hash_hex = "0x" + hash_hex

    return {
        "tx_hash": hash_hex,
        "status": "confirmed" if receipt.status == 1 else "failed",
        "block_number": receipt.blockNumber,
        "explorer_url": f"{settings.BASESCAN_TX_URL}{hash_hex}",
    }
