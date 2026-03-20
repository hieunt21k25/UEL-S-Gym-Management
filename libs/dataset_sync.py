"""
libs/dataset_sync.py
────────────────────
Syncs live SQLite data → dataset/*.json after every write operation.

Usage (called from route handlers after commit):
    from libs.dataset_sync import sync_members, sync_payments, ...
    sync_members(db)

Each sync_*() function:
  - Queries ALL rows from the database for that table
  - Serialises to a clean JSON list
  - Atomically writes to dataset/<file>.json (write to .tmp then rename)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

_DATASET = Path(__file__).resolve().parent.parent / "dataset"


def _write(filename: str, data: list[Any]) -> None:
    """Atomically write data to dataset/<filename>."""
    path = _DATASET / filename
    tmp  = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)


# ── Members ──────────────────────────────────────────────────────────────────

def sync_members(db: Session) -> None:
    from model import models
    rows = db.query(models.Member).order_by(models.Member.id).all()
    _write("members.json", [
        {
            "id":        r.id,
            "full_name": r.full_name,
            "phone":     r.phone or "",
            "email":     r.email,
            "dob":       str(r.dob) if r.dob else None,
            "gender":    r.gender.value if r.gender else "other",
            "join_date": str(r.join_date) if r.join_date else None,
            "status":    r.status.value if r.status else "active",
        }
        for r in rows
    ])


# ── Packages ─────────────────────────────────────────────────────────────────

def sync_packages(db: Session) -> None:
    from model import models
    rows = db.query(models.Package).order_by(models.Package.id).all()
    _write("packages.json", [
        {
            "id":             r.id,
            "name":           r.name,
            "duration_unit":  r.duration_unit.value,
            "duration_value": r.duration_value,
            "price":          r.price,
            "description":    r.description or "",
        }
        for r in rows
    ])


# ── Trainers ─────────────────────────────────────────────────────────────────

def sync_trainers(db: Session) -> None:
    from model import models
    rows = db.query(models.Trainer).order_by(models.Trainer.id).all()
    _write("trainers.json", [
        {
            "id":                    r.id,
            "full_name":             r.full_name,
            "phone":                 r.phone or "",
            "specialty":             r.specialty or "",
            "availability_schedule": r.availability_schedule or "",
        }
        for r in rows
    ])


# ── Subscriptions ─────────────────────────────────────────────────────────────

def sync_subscriptions(db: Session) -> None:
    from model import models
    rows = db.query(models.Subscription).order_by(models.Subscription.id).all()
    _write("subscriptions.json", [
        {
            "id":         r.id,
            "member_id":  r.member_id,
            "package_id": r.package_id,
            "start_date": str(r.start_date),
            "end_date":   str(r.end_date),
            "status":     r.status.value,
        }
        for r in rows
    ])


# ── Check-ins ─────────────────────────────────────────────────────────────────

def sync_checkins(db: Session) -> None:
    from model import models
    rows = db.query(models.CheckIn).order_by(models.CheckIn.id).all()
    _write("checkins.json", [
        {
            "id":        r.id,
            "member_id": r.member_id,
            "timestamp": r.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        for r in rows
    ])


# ── Payments ──────────────────────────────────────────────────────────────────

def sync_payments(db: Session) -> None:
    from model import models
    rows = db.query(models.Payment).order_by(models.Payment.id).all()
    _write("payments.json", [
        {
            "id":              r.id,
            "member_id":       r.member_id,
            "subscription_id": r.related_subscription_id,
            "amount":          r.amount,
            "method":          r.method.value,
            "date":            str(r.date),
            "note":            r.note or "",
        }
        for r in rows
    ])


# ── Plans ─────────────────────────────────────────────────────────────────────

def sync_plans(db: Session) -> None:
    from model import models
    rows = db.query(models.TrainingPlan).order_by(models.TrainingPlan.id).all()
    _write("plans.json", [
        {
            "id":              r.id,
            "member_id":       r.member_id,
            "trainer_id":      r.trainer_id,
            "goal":            r.goal or "",
            "weekly_schedule": json.loads(r.weekly_schedule_json or "{}"),
            "notes":           r.notes or "",
        }
        for r in rows
    ])
