"""Check-in routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_checkins

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.post("", response_model=schemas.CheckInRead, status_code=201)
def create_checkin(payload: schemas.CheckInCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Check in a member — rejects if no active subscription."""
    if not crud.get_member(db, payload.member_id):
        raise HTTPException(404, "Member not found")
    if not crud.has_active_subscription(db, payload.member_id):
        raise HTTPException(400, "Member has no active subscription")
    c = crud.create_checkin(db, payload)
    sync_checkins(db)
    return c


@router.get("", response_model=List[schemas.CheckInRead])
def list_checkins(member_id: Optional[int] = None, limit: int = 500, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_checkins(db, member_id, limit)


@router.get("/stats", response_model=schemas.CheckInStats)
def checkin_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Return daily / weekly / monthly check-in counts."""
    return crud.get_checkin_stats(db)
