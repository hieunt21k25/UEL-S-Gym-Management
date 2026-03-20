"""Package CRUD routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user, require_admin
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_packages

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("", response_model=List[schemas.PackageRead])
def list_packages(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_packages(db)


@router.get("/{pkg_id}", response_model=schemas.PackageRead)
def get_package(pkg_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.get_package(db, pkg_id)
    if not p:
        raise HTTPException(404, "Package not found")
    return p


@router.post("", response_model=schemas.PackageRead, status_code=201)
def create_package(payload: schemas.PackageCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p = crud.create_package(db, payload)
    sync_packages(db)
    return p


@router.put("/{pkg_id}", response_model=schemas.PackageRead)
def update_package(pkg_id: int, payload: schemas.PackageUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    p = crud.update_package(db, pkg_id, payload)
    if not p:
        raise HTTPException(404, "Package not found")
    sync_packages(db)
    return p


@router.delete("/{pkg_id}", status_code=204)
def delete_package(pkg_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not crud.delete_package(db, pkg_id):
        raise HTTPException(404, "Package not found")
    sync_packages(db)
