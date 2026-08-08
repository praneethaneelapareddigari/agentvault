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


settings = Settings()
