"""CRUD helper functions used by route handlers."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from model import models, schemas
from model.auth import hash_password


# ── Users ──────────────────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Members ────────────────────────────────────────────────────────────────────

def get_members(
    db: Session,
    status: Optional[str] = None,
    join_date_from: Optional[date] = None,
    join_date_to: Optional[date] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[models.Member]:
    q = db.query(models.Member)
    if status:
        q = q.filter(models.Member.status == status)
    if join_date_from:
        q = q.filter(models.Member.join_date >= join_date_from)
    if join_date_to:
        q = q.filter(models.Member.join_date <= join_date_to)
    if search:
        like = f"%{search}%"
        q = q.filter(
            models.Member.full_name.ilike(like) | models.Member.email.ilike(like)
        )
    return q.offset(skip).limit(limit).all()


def get_member(db: Session, member_id: int) -> Optional[models.Member]:
    return db.query(models.Member).get(member_id)


def create_member(db: Session, payload: schemas.MemberCreate) -> models.Member:
    member = models.Member(**payload.model_dump())
    if not member.join_date:
        member.join_date = date.today()
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: int, payload: schemas.MemberUpdate) -> Optional[models.Member]:
    member = get_member(db, member_id)
    if not member:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(member, k, v)
    db.commit()
    db.refresh(member)
    return member


def delete_member(db: Session, member_id: int) -> bool:
    member = get_member(db, member_id)
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True


# ── Packages ───────────────────────────────────────────────────────────────────

def get_packages(db: Session) -> List[models.Package]:
    return db.query(models.Package).all()


def get_package(db: Session, pkg_id: int) -> Optional[models.Package]:
    return db.query(models.Package).get(pkg_id)


def create_package(db: Session, payload: schemas.PackageCreate) -> models.Package:
    pkg = models.Package(**payload.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def update_package(db: Session, pkg_id: int, payload: schemas.PackageUpdate) -> Optional[models.Package]:
    pkg = get_package(db, pkg_id)
    if not pkg:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pkg, k, v)
    db.commit()
    db.refresh(pkg)
    return pkg


def delete_package(db: Session, pkg_id: int) -> bool:
    pkg = get_package(db, pkg_id)
    if not pkg:
        return False
    db.delete(pkg)
    db.commit()
    return True


# ── Subscriptions ──────────────────────────────────────────────────────────────

def _calc_end_date(start: date, pkg: models.Package) -> date:
    if pkg.duration_unit == models.DurationUnit.days:
        return start + timedelta(days=pkg.duration_value)
    return start + relativedelta(months=pkg.duration_value)


def get_subscriptions(db: Session, member_id: Optional[int] = None) -> List[models.Subscription]:
    q = db.query(models.Subscription)
    if member_id:
        q = q.filter(models.Subscription.member_id == member_id)
    return q.all()


def get_subscription(db: Session, sub_id: int) -> Optional[models.Subscription]:
    return db.query(models.Subscription).get(sub_id)


def create_subscription(db: Session, payload: schemas.SubscriptionCreate) -> models.Subscription:
    pkg = get_package(db, payload.package_id)
    end = payload.end_date or _calc_end_date(payload.start_date, pkg)
    sub = models.Subscription(
        member_id=payload.member_id,
        package_id=payload.package_id,
        start_date=payload.start_date,
        end_date=end,
        status=models.SubStatus.active,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_subscription(db: Session, sub_id: int, payload: schemas.SubscriptionUpdate) -> Optional[models.Subscription]:
    sub = get_subscription(db, sub_id)
    if not sub:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(sub, k, v)
    db.commit()
    db.refresh(sub)
    return sub


def refresh_expired_subscriptions(db: Session) -> int:
    """Set status=expired for all subscriptions past end_date. Returns count updated."""
    today = date.today()
    expired = db.query(models.Subscription).filter(
        models.Subscription.end_date < today,
        models.Subscription.status == models.SubStatus.active,
    ).all()
    for sub in expired:
        sub.status = models.SubStatus.expired
    db.commit()
    return len(expired)


def has_active_subscription(db: Session, member_id: int) -> bool:
    today = date.today()
    return db.query(models.Subscription).filter(
        models.Subscription.member_id == member_id,
        models.Subscription.status == models.SubStatus.active,
        models.Subscription.start_date <= today,
        models.Subscription.end_date >= today,
    ).first() is not None


# ── Check-ins ─────────────────────────────────────────────────────────────────

def create_checkin(db: Session, payload: schemas.CheckInCreate) -> models.CheckIn:
    from datetime import datetime, timezone
    checkin = models.CheckIn(
        member_id=payload.member_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def get_checkins(db: Session, member_id: Optional[int] = None, limit: int = 500) -> List[models.CheckIn]:
    q = db.query(models.CheckIn)
    if member_id:
        q = q.filter(models.CheckIn.member_id == member_id)
    return q.order_by(models.CheckIn.timestamp.desc()).limit(limit).all()


def get_checkin_stats(db: Session) -> schemas.CheckInStats:
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    def count(since):
        return db.query(models.CheckIn).filter(models.CheckIn.timestamp >= since).count()

    return schemas.CheckInStats(
        daily=count(today_start),
        weekly=count(week_start),
        monthly=count(month_start),
    )


# ── Payments ───────────────────────────────────────────────────────────────────

def get_payments(db: Session, member_id: Optional[int] = None) -> List[models.Payment]:
    q = db.query(models.Payment)
    if member_id:
        q = q.filter(models.Payment.member_id == member_id)
    return q.order_by(models.Payment.date.desc()).all()


def get_payment(db: Session, pay_id: int) -> Optional[models.Payment]:
    return db.query(models.Payment).get(pay_id)


def create_payment(db: Session, payload: schemas.PaymentCreate) -> models.Payment:
    pay = models.Payment(**payload.model_dump())
    if not pay.date:
        pay.date = date.today()
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return pay


def update_payment(db: Session, pay_id: int, payload: schemas.PaymentUpdate) -> Optional[models.Payment]:
    pay = get_payment(db, pay_id)
    if not pay:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pay, k, v)
    db.commit()
    db.refresh(pay)
    return pay


def delete_payment(db: Session, pay_id: int) -> bool:
    pay = get_payment(db, pay_id)
    if not pay:
        return False
    db.delete(pay)
    db.commit()
    return True


def generate_invoice(db: Session, payment_id: int) -> Optional[models.Invoice]:
    pay = get_payment(db, payment_id)
    if not pay:
        return None
    existing = db.query(models.Invoice).filter(models.Invoice.payment_id == payment_id).first()
    if existing:
        return existing
    member = get_member(db, pay.member_id)
    pkg_name = ""
    if pay.related_subscription_id:
        sub = get_subscription(db, pay.related_subscription_id)
        if sub and sub.package:
            pkg_name = sub.package.name
    invoice_no = f"INV-{payment_id:06d}"
    inv = models.Invoice(
        invoice_no=invoice_no,
        payment_id=payment_id,
        member_name=member.full_name if member else "Unknown",
        package_name=pkg_name,
        total=pay.amount,
        status=models.InvoiceStatus.paid,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


# ── Trainers ───────────────────────────────────────────────────────────────────

def get_trainers(db: Session) -> List[models.Trainer]:
    return db.query(models.Trainer).all()


def get_trainer(db: Session, trainer_id: int) -> Optional[models.Trainer]:
    return db.query(models.Trainer).get(trainer_id)


def create_trainer(db: Session, payload: schemas.TrainerCreate) -> models.Trainer:
    t = models.Trainer(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_trainer(db: Session, trainer_id: int, payload: schemas.TrainerUpdate) -> Optional[models.Trainer]:
    t = get_trainer(db, trainer_id)
    if not t:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


def delete_trainer(db: Session, trainer_id: int) -> bool:
    t = get_trainer(db, trainer_id)
    if not t:
        return False
    db.delete(t)
    db.commit()
    return True


# ── Plans ──────────────────────────────────────────────────────────────────────

def get_plans(db: Session, member_id: Optional[int] = None) -> List[models.TrainingPlan]:
    q = db.query(models.TrainingPlan)
    if member_id:
        q = q.filter(models.TrainingPlan.member_id == member_id)
    return q.all()


def get_plan(db: Session, plan_id: int) -> Optional[models.TrainingPlan]:
    return db.query(models.TrainingPlan).get(plan_id)


def create_plan(db: Session, payload: schemas.PlanCreate) -> models.TrainingPlan:
    plan = models.TrainingPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan_id: int, payload: schemas.PlanUpdate) -> Optional[models.TrainingPlan]:
    plan = get_plan(db, plan_id)
    if not plan:
        return None
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> bool:
    plan = get_plan(db, plan_id)
    if not plan:
        return False
    db.delete(plan)
    db.commit()
    return True
