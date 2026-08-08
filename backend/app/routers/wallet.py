from fastapi import APIRouter
from app.services import wallet_service

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.get("/{address}/balances")
def get_balances(address: str):
    return {
        "address": address,
        "balances": wallet_service.get_balances(address),
        "total_usd": wallet_service.get_total_usd(address),
    }
