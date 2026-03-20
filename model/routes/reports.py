"""Reports & Dashboard routes."""

from __future__ import annotations

from datetime import date, timedelta, datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from model import models, schemas
from model.auth import get_current_user
from model.db import get_db
from model.models import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Aggregate stats for the dashboard cards."""
    active_members = db.query(models.Member).filter(models.Member.status == "active").count()
    active_subs = db.query(models.Subscription).filter(models.Subscription.status == "active").count()
    expired_subs = db.query(models.Subscription).filter(models.Subscription.status == "expired").count()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_checkins = db.query(models.CheckIn).filter(models.CheckIn.timestamp >= today_start).count()

    total_revenue = db.query(func.sum(models.Payment.amount)).scalar() or 0.0

    return schemas.DashboardStats(
        total_active_members=active_members,
        active_subscriptions=active_subs,
        expired_subscriptions=expired_subs,
        today_checkins=today_checkins,
        total_revenue=round(float(total_revenue), 2),
    )


@router.get("/revenue_monthly", response_model=List[schemas.MonthlyRevenue])
def revenue_monthly(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Last 12 months revenue grouped by month."""
    results = (
        db.query(
            extract("year", models.Payment.date).label("yr"),
            extract("month", models.Payment.date).label("mo"),
            func.sum(models.Payment.amount).label("total"),
        )
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    return [
        schemas.MonthlyRevenue(
            month=f"{int(r.yr)}-{int(r.mo):02d}",
            revenue=round(float(r.total), 2),
        )
        for r in results[-12:]
    ]


@router.get("/top_checkins", response_model=List[schemas.TopMember])
def top_checkins(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Top 5 members by check-ins this month."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        db.query(
            models.CheckIn.member_id,
            func.count(models.CheckIn.id).label("cnt"),
        )
        .filter(models.CheckIn.timestamp >= month_start)
        .group_by(models.CheckIn.member_id)
        .order_by(func.count(models.CheckIn.id).desc())
        .limit(5)
        .all()
    )
    result = []
    for row in rows:
        member = db.query(models.Member).get(row.member_id)
        result.append(schemas.TopMember(
            member_id=row.member_id,
            full_name=member.full_name if member else "Unknown",
            checkin_count=row.cnt,
        ))
    return result
