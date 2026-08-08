"""
Aave V3 integration — the one real DeFi protocol AgentVault targets in this
build (deliberately one, not fifteen — see product spec section 7,
"at least one real integration is enough"). Pool address is Aave's V3
Pool Proxy on Base Sepolia; see app/config.py for the verified address.
"""
from app.config import settings

AAVE_POOL_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address", "name": "onBehalfOf", "type": "address"},
            {"internalType": "uint16", "name": "referralCode", "type": "uint16"},
        ],
        "name": "supply",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def encode_supply_calldata(w3, asset: str, amount_wei: int, on_behalf_of: str) -> bytes:
    """Encodes the exact calldata for Aave V3 Pool.supply(), which is what
    PolicyVault.executeIfApproved() forwards on-chain."""
    pool = w3.eth.contract(
        address=w3.to_checksum_address(settings.AAVE_POOL_ADDRESS), abi=AAVE_POOL_ABI
    )
    return pool.encode_abi(
        abi_element_identifier="supply",
        args=[w3.to_checksum_address(asset), amount_wei, w3.to_checksum_address(on_behalf_of), 0],
    )
