"""Member CRUD routes."""

from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_members

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=List[schemas.MemberRead])
def list_members(
    status: Optional[str] = None,
    join_date_from: Optional[date] = Query(None),
    join_date_to: Optional[date] = Query(None),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.get_members(db, status, join_date_from, join_date_to, search, skip, limit)


@router.get("/{member_id}", response_model=schemas.MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    m = crud.get_member(db, member_id)
    if not m:
        raise HTTPException(404, "Member not found")
    return m


@router.post("", response_model=schemas.MemberRead, status_code=201)
def create_member(payload: schemas.MemberCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    m = crud.create_member(db, payload)
    sync_members(db)
    return m


@router.put("/{member_id}", response_model=schemas.MemberRead)
def update_member(member_id: int, payload: schemas.MemberUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    m = crud.update_member(db, member_id, payload)
    if not m:
        raise HTTPException(404, "Member not found")
    sync_members(db)
    return m


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not crud.delete_member(db, member_id):
        raise HTTPException(404, "Member not found")
    sync_members(db)
