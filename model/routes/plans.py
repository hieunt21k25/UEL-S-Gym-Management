"""Training Plan CRUD routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_plans

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=List[schemas.PlanRead])
def list_plans(member_id: Optional[int] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_plans(db, member_id)


@router.get("/{plan_id}", response_model=schemas.PlanRead)
def get_plan(plan_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.get_plan(db, plan_id)
    if not p:
        raise HTTPException(404, "Plan not found")
    return p


@router.post("", response_model=schemas.PlanRead, status_code=201)
def create_plan(payload: schemas.PlanCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.create_plan(db, payload)
    sync_plans(db)
    return p


@router.put("/{plan_id}", response_model=schemas.PlanRead)
def update_plan(plan_id: int, payload: schemas.PlanUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.update_plan(db, plan_id, payload)
    if not p:
        raise HTTPException(404, "Plan not found")
    sync_plans(db)
    return p


@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not crud.delete_plan(db, plan_id):
        raise HTTPException(404, "Plan not found")
    sync_plans(db)
