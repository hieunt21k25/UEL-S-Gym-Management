"""
model/seed.py
─────────────
Seed the database with demo data loaded from dataset/*.json.

Usage:
    # Upsert (default — safe to run multiple times):
    python -m model.seed

    # Full reset (drops all tables then re-seeds):
    python -m model.seed --reset

Rules:
    - ALL seed data lives in dataset/*.json — no hardcoded lists here.
    - Data is upserted by stable JSON `id` fields.
    - Invoices are auto-generated for every payment.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

from model.db import SessionLocal, engine
from model.models import Base
from model import models
from model.auth import hash_password
from libs.data_loader import load_json, validate_required


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")


# ── Section seeders ───────────────────────────────────────────────────────────

def seed_users(db) -> None:
    records = load_json("users.json")
    for r in records:
        validate_required(r, ["id", "username", "email", "password", "role"], "users.json")
        obj = db.query(models.User).filter_by(id=r["id"]).first()
        if obj:
            obj.username      = r["username"]
            obj.email         = r["email"]
            obj.password_hash = hash_password(r["password"])
            obj.role          = models.UserRole(r["role"])
        else:
            db.add(models.User(
                id            = r["id"],
                username      = r["username"],
                email         = r["email"],
                password_hash = hash_password(r["password"]),
                role          = models.UserRole(r["role"]),
            ))
    db.commit()
    print(f"  ✓ users       ({len(records)} records)")


def seed_packages(db) -> None:
    records = load_json("packages.json")
    for r in records:
        validate_required(r, ["id", "name", "duration_unit", "duration_value", "price"], "packages.json")
        obj = db.query(models.Package).filter_by(id=r["id"]).first()
        if obj:
            obj.name           = r["name"]
            obj.duration_unit  = models.DurationUnit(r["duration_unit"])
            obj.duration_value = r["duration_value"]
            obj.price          = r["price"]
            obj.description    = r.get("description", "")
        else:
            db.add(models.Package(
                id             = r["id"],
                name           = r["name"],
                duration_unit  = models.DurationUnit(r["duration_unit"]),
                duration_value = r["duration_value"],
                price          = r["price"],
                description    = r.get("description", ""),
            ))
    db.commit()
    print(f"  ✓ packages    ({len(records)} records)")


def seed_trainers(db) -> None:
    records = load_json("trainers.json")
    for r in records:
        validate_required(r, ["id", "full_name"], "trainers.json")
        obj = db.query(models.Trainer).filter_by(id=r["id"]).first()
        if obj:
            obj.full_name             = r["full_name"]
            obj.phone                 = r.get("phone", "")
            obj.specialty             = r.get("specialty", "")
            obj.availability_schedule = r.get("availability_schedule", "")
        else:
            db.add(models.Trainer(
                id                    = r["id"],
                full_name             = r["full_name"],
                phone                 = r.get("phone", ""),
                specialty             = r.get("specialty", ""),
                availability_schedule = r.get("availability_schedule", ""),
            ))
    db.commit()
    print(f"  ✓ trainers    ({len(records)} records)")


def seed_members(db) -> None:
    records = load_json("members.json")
    for r in records:
        validate_required(r, ["id", "full_name", "email"], "members.json")
        obj = db.query(models.Member).filter_by(id=r["id"]).first()
        if obj:
            obj.full_name = r["full_name"]
            obj.phone     = r.get("phone", "")
            obj.email     = r["email"]
            obj.dob       = _parse_date(r["dob"])       if r.get("dob")       else None
            obj.gender    = models.GenderEnum(r["gender"]) if r.get("gender") else models.GenderEnum.other
            obj.join_date = _parse_date(r["join_date"]) if r.get("join_date") else date.today()
            obj.status    = models.MemberStatus(r.get("status", "active"))
        else:
            db.add(models.Member(
                id        = r["id"],
                full_name = r["full_name"],
                phone     = r.get("phone", ""),
                email     = r["email"],
                dob       = _parse_date(r["dob"])       if r.get("dob")       else None,
                gender    = models.GenderEnum(r["gender"]) if r.get("gender") else models.GenderEnum.other,
                join_date = _parse_date(r["join_date"]) if r.get("join_date") else date.today(),
                status    = models.MemberStatus(r.get("status", "active")),
            ))
    db.commit()
    print(f"  ✓ members     ({len(records)} records)")


def seed_subscriptions(db) -> None:
    records = load_json("subscriptions.json")
    for r in records:
        validate_required(r, ["id", "member_id", "package_id", "start_date", "end_date"], "subscriptions.json")
        obj = db.query(models.Subscription).filter_by(id=r["id"]).first()
        if obj:
            obj.member_id  = r["member_id"]
            obj.package_id = r["package_id"]
            obj.start_date = _parse_date(r["start_date"])
            obj.end_date   = _parse_date(r["end_date"])
            obj.status     = models.SubStatus(r.get("status", "active"))
        else:
            db.add(models.Subscription(
                id         = r["id"],
                member_id  = r["member_id"],
                package_id = r["package_id"],
                start_date = _parse_date(r["start_date"]),
                end_date   = _parse_date(r["end_date"]),
                status     = models.SubStatus(r.get("status", "active")),
            ))
    db.commit()
    print(f"  ✓ subscriptions ({len(records)} records)")


def seed_checkins(db) -> None:
    records = load_json("checkins.json")
    for r in records:
        validate_required(r, ["id", "member_id", "timestamp"], "checkins.json")
        obj = db.query(models.CheckIn).filter_by(id=r["id"]).first()
        if obj:
            obj.member_id = r["member_id"]
            obj.timestamp = _parse_dt(r["timestamp"])
        else:
            db.add(models.CheckIn(
                id        = r["id"],
                member_id = r["member_id"],
                timestamp = _parse_dt(r["timestamp"]),
            ))
    db.commit()
    print(f"  ✓ checkins    ({len(records)} records)")


def seed_payments(db) -> None:
    records = load_json("payments.json")
    for r in records:
        validate_required(r, ["id", "member_id", "amount", "method", "date"], "payments.json")
        obj = db.query(models.Payment).filter_by(id=r["id"]).first()
        sub_id = r.get("subscription_id")
        if obj:
            obj.member_id               = r["member_id"]
            obj.amount                  = r["amount"]
            obj.method                  = models.PaymentMethod(r["method"])
            obj.date                    = _parse_date(r["date"])
            obj.note                    = r.get("note", "")
            obj.related_subscription_id = sub_id
        else:
            pay = models.Payment(
                id                      = r["id"],
                member_id               = r["member_id"],
                amount                  = r["amount"],
                method                  = models.PaymentMethod(r["method"]),
                date                    = _parse_date(r["date"]),
                note                    = r.get("note", ""),
                related_subscription_id = sub_id,
            )
            db.add(pay)
            db.flush()

            # Auto-generate invoice for each payment
            if not db.query(models.Invoice).filter_by(payment_id=pay.id).first():
                member  = db.query(models.Member).filter_by(id=pay.member_id).first()
                sub     = db.query(models.Subscription).filter_by(id=sub_id).first() if sub_id else None
                pkg_name = sub.package.name if (sub and sub.package) else "N/A"
                db.add(models.Invoice(
                    invoice_no  = f"INV-{pay.id:06d}",
                    payment_id  = pay.id,
                    member_name = member.full_name if member else "—",
                    package_name= pkg_name,
                    total       = pay.amount,
                    status      = models.InvoiceStatus.paid,
                ))
    db.commit()
    print(f"  ✓ payments    ({len(records)} records + invoices)")


def seed_plans(db) -> None:
    records = load_json("plans.json")
    for r in records:
        validate_required(r, ["id", "member_id", "trainer_id", "goal"], "plans.json")
        weekly = r.get("weekly_schedule", {})
        obj = db.query(models.TrainingPlan).filter_by(id=r["id"]).first()
        if obj:
            obj.member_id           = r["member_id"]
            obj.trainer_id          = r["trainer_id"]
            obj.goal                = r["goal"]
            obj.weekly_schedule_json = json.dumps(weekly)
            obj.notes               = r.get("notes", "")
        else:
            db.add(models.TrainingPlan(
                id                   = r["id"],
                member_id            = r["member_id"],
                trainer_id           = r["trainer_id"],
                goal                 = r["goal"],
                weekly_schedule_json = json.dumps(weekly),
                notes                = r.get("notes", ""),
            ))
    db.commit()
    print(f"  ✓ plans       ({len(records)} records)")


# ── Entry point ───────────────────────────────────────────────────────────────

def run_seed(reset: bool = False) -> None:
    """Create tables and upsert demo data from dataset/*.json."""
    if reset:
        print("⚠  Dropping all tables…")
        Base.metadata.drop_all(bind=engine)
        print("   Done.\n")

    print("Creating tables (if needed)…")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\nSeeding from dataset/:")
        seed_users(db)
        seed_packages(db)
        seed_trainers(db)
        seed_members(db)
        seed_subscriptions(db)
        seed_checkins(db)
        seed_payments(db)
        seed_plans(db)
    finally:
        db.close()

    print("\n✅  Seed complete.")
    print("   Edit dataset/*.json to change demo data.")
    print("   Run 'python -m model.seed' to re-apply.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed FlexTrack database from dataset/*.json")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--reset",  action="store_true", help="Drop all tables then re-seed from scratch")
    group.add_argument("--upsert", action="store_true", help="Upsert only (default behaviour)")
    args = parser.parse_args()
    run_seed(reset=args.reset)
