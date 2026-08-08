from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("/{tx_id}/status", response_model=schemas.TransactionOut)
def get_tx_status(tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter_by(id=tx_id).first()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return tx
