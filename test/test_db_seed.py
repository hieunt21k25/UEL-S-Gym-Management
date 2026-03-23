"""DB seed verification tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from model.db import SessionLocal, engine
from model.models import Base, User, Member, Package, Subscription, CheckIn, Payment, Trainer, TrainingPlan
from model.seed import run_seed


@pytest.fixture(scope="module", autouse=True)
def seeded_db():
    Base.metadata.create_all(bind=engine)
    run_seed()
    yield


def test_users_seeded():
    db = SessionLocal()
    count = db.query(User).count()
    db.close()
    assert count >= 2, "Expected at least 2 users (admin, staff)"


def test_members_seeded():
    db = SessionLocal()
    count = db.query(Member).count()
    db.close()
    assert count >= 20


def test_packages_seeded():
    db = SessionLocal()
    count = db.query(Package).count()
    db.close()
    assert count >= 5


def test_subscriptions_seeded():
    db = SessionLocal()
    count = db.query(Subscription).count()
    db.close()
    assert count >= 20


def test_checkins_seeded():
    db = SessionLocal()
    count = db.query(CheckIn).count()
    db.close()
    assert count >= 50


def test_payments_seeded():
    db = SessionLocal()
    count = db.query(Payment).count()
    db.close()
    assert count >= 30


def test_trainers_seeded():
    db = SessionLocal()
    count = db.query(Trainer).count()
    db.close()
    assert count >= 5


def test_plans_seeded():
    db = SessionLocal()
    count = db.query(TrainingPlan).count()
    db.close()
    assert count >= 10


def test_admin_password():
    from model.auth import verify_password
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    db.close()
    assert admin is not None
    assert verify_password("admin123", admin.password_hash)


def test_staff_password():
    from model.auth import verify_password
    db = SessionLocal()
    staff = db.query(User).filter(User.username == "staff").first()
    db.close()
    assert staff is not None
    assert verify_password("staff123", staff.password_hash)
