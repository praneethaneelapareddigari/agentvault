"""
Shared Base Sepolia RPC connection helper. Every real-chain-reading module
(wallet balances, simulation, execution) goes through this single function
so there's exactly one place that decides whether we're connected to a
live chain, and every caller degrades gracefully to its mock/fallback path
if not.
"""
from app.config import settings

_cached_w3 = None
_attempted = False


def get_web3():
    """Returns a connected Web3 instance, or None if real-chain access
    isn't configured or isn't reachable. Result is cached for the process
    lifetime (avoids re-dialing the RPC on every request)."""
    global _cached_w3, _attempted
    if _attempted:
        return _cached_w3
    _attempted = True

    if not settings.BASE_SEPOLIA_RPC_URL:
        return None
    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(settings.BASE_SEPOLIA_RPC_URL, request_kwargs={"timeout": 6}))
        if w3.is_connected():
            _cached_w3 = w3
            return w3
    except Exception:
        pass
    return None
