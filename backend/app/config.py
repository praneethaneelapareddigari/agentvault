"""
Central configuration. Loaded once, imported everywhere.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agentvault.db")
    SUPPORTED_CHAINS: list[str] = os.getenv(
        "SUPPORTED_CHAINS", "ethereum,base,arbitrum"
    ).split(",")
    PRIMARY_CHAIN: str = os.getenv("PRIMARY_CHAIN", "base")

    # --- Hardcoded demo defaults ---
    DEMO_WALLET_ADDRESS: str = "0xDEMO0000000000000000000000000000000001"
    DEMO_ASSET: str = "USDC"

    # --- Real on-chain execution (Base Sepolia) ---
    # Defaults to "mock" so the app runs end-to-end with zero setup. Set to
    # "real" once BASE_SEPOLIA_RPC_URL, RELAYER_PRIVATE_KEY,
    # POLICY_VAULT_ADDRESS, and USDC_ADDRESS_BASE_SEPOLIA are all configured
    # (see .env.example) to send actual transactions on Base Sepolia.
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "mock")
    BASE_SEPOLIA_RPC_URL: str | None = os.getenv("BASE_SEPOLIA_RPC_URL") or None
    RELAYER_PRIVATE_KEY: str | None = os.getenv("RELAYER_PRIVATE_KEY") or None
    POLICY_VAULT_ADDRESS: str | None = os.getenv("POLICY_VAULT_ADDRESS") or None
    # Aave V3 Pool Proxy, Base Sepolia (proto_base_sepolia_v3 market) —
    # verified: https://sepolia.basescan.org/address/0xA238Dd80C259a72e81d7e4664a9801593F98d1c5
    AAVE_POOL_ADDRESS: str = os.getenv(
        "AAVE_POOL_ADDRESS", "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
    )
    USDC_ADDRESS: str | None = os.getenv("USDC_ADDRESS_BASE_SEPOLIA") or None
    BASE_SEPOLIA_CHAIN_ID: int = 84532
    BASESCAN_TX_URL: str = "https://sepolia.basescan.org/tx/"


settings = Settings()
