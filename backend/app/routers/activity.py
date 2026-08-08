from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("/by-wallet/{wallet_address}")
def get_activity_by_wallet(wallet_address: str, db: Session = Depends(get_db)):
    """Convenience lookup so the frontend doesn't need to track internal
    user ids — it only ever knows the connected wallet address."""
    user = db.query(models.User).filter_by(wallet_address=wallet_address).first()
    if not user:
        return []
    return get_activity(user.id, db)


@router.get("/{user_id}")
def get_activity(user_id: str, db: Session = Depends(get_db)):
    logs = (
        db.query(models.ActivityLog)
        .filter_by(user_id=user_id)
        .order_by(models.ActivityLog.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": l.id,
            "event_type": l.event_type,
            "detail": l.detail,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
