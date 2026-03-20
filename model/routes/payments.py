"""Payment and Invoice routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from model import crud, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User
from libs.dataset_sync import sync_payments

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=List[schemas.PaymentRead])
def list_payments(member_id: Optional[int] = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return crud.get_payments(db, member_id)


@router.get("/{pay_id}", response_model=schemas.PaymentRead)
def get_payment(pay_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.get_payment(db, pay_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.post("", response_model=schemas.PaymentRead, status_code=201)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.create_payment(db, payload)
    sync_payments(db)
    return p


@router.put("/{pay_id}", response_model=schemas.PaymentRead)
def update_payment(pay_id: int, payload: schemas.PaymentUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = crud.update_payment(db, pay_id, payload)
    if not p:
        raise HTTPException(404, "Payment not found")
    sync_payments(db)
    return p


@router.delete("/{pay_id}", status_code=204)
def delete_payment(pay_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not crud.delete_payment(db, pay_id):
        raise HTTPException(404, "Payment not found")
    sync_payments(db)


@router.post("/{pay_id}/invoice", response_model=schemas.InvoiceRead)
def generate_invoice(pay_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Generate (or return existing) invoice for a payment."""
    inv = crud.generate_invoice(db, pay_id)
    if not inv:
        raise HTTPException(404, "Payment not found")
    return inv
