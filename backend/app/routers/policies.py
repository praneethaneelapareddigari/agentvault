from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("/{user_id}")
def get_policy(user_id: str, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter_by(user_id=user_id).first()
    if not policy:
        raise HTTPException(404, "No policy found for user")
    return policy


@router.put("/{user_id}")
def update_policy(user_id: str, body: schemas.PolicyUpdate, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter_by(user_id=user_id).first()
    if not policy:
        raise HTTPException(404, "No policy found for user")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy
