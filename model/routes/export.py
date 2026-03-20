"""CSV Export routes."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from model import models
from model.auth import get_current_user
from model.db import get_db
from model.models import User

router = APIRouter(prefix="/export", tags=["export"])


def _stream_csv(headers: list, rows: list, filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/payments.csv")
def export_payments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Export all payments as CSV."""
    payments = db.query(models.Payment).order_by(models.Payment.date.desc()).all()
    headers = ["id", "member_id", "amount", "method", "date", "note", "subscription_id"]
    rows = [
        [p.id, p.member_id, p.amount, p.method.value, str(p.date), p.note, p.related_subscription_id]
        for p in payments
    ]
    return _stream_csv(headers, rows, "payments.csv")


@router.get("/checkins.csv")
def export_checkins(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Export all check-ins as CSV."""
    checkins = db.query(models.CheckIn).order_by(models.CheckIn.timestamp.desc()).all()
    headers = ["id", "member_id", "timestamp"]
    rows = [[c.id, c.member_id, str(c.timestamp)] for c in checkins]
    return _stream_csv(headers, rows, "checkins.csv")
