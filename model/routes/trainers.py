"""Trainer CRUD routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_trainers

router = APIRouter(prefix="/trainers", tags=["trainers"])


@router.get("", response_model=List[schemas.TrainerRead])
def list_trainers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_trainers(db)


@router.get("/{trainer_id}", response_model=schemas.TrainerRead)
def get_trainer(trainer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = crud.get_trainer(db, trainer_id)
    if not t:
        raise HTTPException(404, "Trainer not found")
    return t


@router.post("", response_model=schemas.TrainerRead, status_code=201)
def create_trainer(payload: schemas.TrainerCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = crud.create_trainer(db, payload)
    sync_trainers(db)
    return t


@router.put("/{trainer_id}", response_model=schemas.TrainerRead)
def update_trainer(trainer_id: int, payload: schemas.TrainerUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    t = crud.update_trainer(db, trainer_id, payload)
    if not t:
        raise HTTPException(404, "Trainer not found")
    sync_trainers(db)
    return t


@router.delete("/{trainer_id}", status_code=204)
def delete_trainer(trainer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not crud.delete_trainer(db, trainer_id):
        raise HTTPException(404, "Trainer not found")
    sync_trainers(db)
