"""Subscription CRUD routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user, require_admin
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_subscriptions

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=List[schemas.SubscriptionRead])
def list_subscriptions(member_id: Optional[int] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_subscriptions(db, member_id)


@router.get("/{sub_id}", response_model=schemas.SubscriptionRead)
def get_subscription(sub_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = crud.get_subscription(db, sub_id)
    if not s:
        raise HTTPException(404, "Subscription not found")
    return s


@router.post("", response_model=schemas.SubscriptionRead, status_code=201)
def create_subscription(payload: schemas.SubscriptionCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not crud.get_member(db, payload.member_id):
        raise HTTPException(404, "Member not found")
    if not crud.get_package(db, payload.package_id):
        raise HTTPException(404, "Package not found")
    s = crud.create_subscription(db, payload)
    sync_subscriptions(db)
    return s


@router.put("/{sub_id}", response_model=schemas.SubscriptionRead)
def update_subscription(sub_id: int, payload: schemas.SubscriptionUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    s = crud.update_subscription(db, sub_id, payload)
    if not s:
        raise HTTPException(404, "Subscription not found")
    sync_subscriptions(db)
    return s


@router.post("/refresh_expired", summary="Mark past-end subscriptions as expired")
def refresh_expired(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    count = crud.refresh_expired_subscriptions(db)
    sync_subscriptions(db)
    return {"updated": count, "detail": f"{count} subscription(s) marked as expired"}
