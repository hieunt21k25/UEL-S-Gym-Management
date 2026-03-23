"""SQLAlchemy ORM models for the Gym Management System."""

from __future__ import annotations

import enum
from datetime import datetime, date

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from model.db import Base


# ── Enums ──────────────────────────────────────────────────────────────────────

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class MemberStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class DurationUnit(str, enum.Enum):
    days = "days"
    months = "months"


class SubStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    bank = "bank"
    card = "card"


class InvoiceStatus(str, enum.Enum):
    paid = "paid"
    unpaid = "unpaid"


class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"


# ── Models ─────────────────────────────────────────────────────────────────────

class User(Base):
    """App user (admin or staff)."""
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(64), unique=True, nullable=False, index=True)
    email: str = Column(String(128), unique=True, nullable=False, index=True)
    password_hash: str = Column(String(256), nullable=False)
    role: UserRole = Column(Enum(UserRole), default=UserRole.staff, nullable=False)
    created_at: datetime = Column(DateTime, default=func.now())


class Member(Base):
    """Gym member."""
    __tablename__ = "members"

    id: int = Column(Integer, primary_key=True, index=True)
    full_name: str = Column(String(128), nullable=False)
    phone: str = Column(String(20))
    email: str = Column(String(128), unique=True, nullable=False, index=True)
    dob: date = Column(Date)
    gender: GenderEnum = Column(Enum(GenderEnum), default=GenderEnum.other)
    join_date: date = Column(Date, default=date.today)
    status: MemberStatus = Column(Enum(MemberStatus), default=MemberStatus.active)

    subscriptions = relationship("Subscription", back_populates="member", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="member", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="member", cascade="all, delete-orphan")
    plans = relationship("TrainingPlan", back_populates="member", cascade="all, delete-orphan")


class Package(Base):
    """Membership package definition."""
    __tablename__ = "packages"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(128), nullable=False)
    duration_unit: DurationUnit = Column(Enum(DurationUnit), nullable=False)
    duration_value: int = Column(Integer, nullable=False)
    price: float = Column(Float, nullable=False)
    description: str = Column(Text, default="")

    subscriptions = relationship("Subscription", back_populates="package")


class Subscription(Base):
    """Links a member to a package for a date range."""
    __tablename__ = "subscriptions"

    id: int = Column(Integer, primary_key=True, index=True)
    member_id: int = Column(Integer, ForeignKey("members.id"), nullable=False)
    package_id: int = Column(Integer, ForeignKey("packages.id"), nullable=False)
    start_date: date = Column(Date, nullable=False)
    end_date: date = Column(Date, nullable=False)
    status: SubStatus = Column(Enum(SubStatus), default=SubStatus.active)

    member = relationship("Member", back_populates="subscriptions")
    package = relationship("Package", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class CheckIn(Base):
    """Member gym check-in record."""
    __tablename__ = "checkins"

    id: int = Column(Integer, primary_key=True, index=True)
    member_id: int = Column(Integer, ForeignKey("members.id"), nullable=False)
    timestamp: datetime = Column(DateTime, default=func.now())

    member = relationship("Member", back_populates="checkins")


class Payment(Base):
    """Payment record."""
    __tablename__ = "payments"

    id: int = Column(Integer, primary_key=True, index=True)
    member_id: int = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount: float = Column(Float, nullable=False)
    method: PaymentMethod = Column(Enum(PaymentMethod), default=PaymentMethod.cash)
    date: date = Column(Date, default=date.today)
    note: str = Column(Text, default="")
    related_subscription_id: int = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    member = relationship("Member", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payment", uselist=False)


class Invoice(Base):
    """Invoice generated for a payment."""
    __tablename__ = "invoices"

    id: int = Column(Integer, primary_key=True, index=True)
    invoice_no: str = Column(String(32), unique=True, nullable=False, index=True)
    payment_id: int = Column(Integer, ForeignKey("payments.id"), nullable=False)
    member_name: str = Column(String(128))
    package_name: str = Column(String(128))
    total: float = Column(Float)
    status: InvoiceStatus = Column(Enum(InvoiceStatus), default=InvoiceStatus.paid)
    created_at: datetime = Column(DateTime, default=func.now())

    payment = relationship("Payment", back_populates="invoice")


class Trainer(Base):
    """Personal trainer."""
    __tablename__ = "trainers"

    id: int = Column(Integer, primary_key=True, index=True)
    full_name: str = Column(String(128), nullable=False)
    phone: str = Column(String(20))
    specialty: str = Column(String(128))
    availability_schedule: str = Column(Text, default="")

    plans = relationship("TrainingPlan", back_populates="trainer")


class TrainingPlan(Base):
    """Personalised training plan for a member."""
    __tablename__ = "training_plans"

    id: int = Column(Integer, primary_key=True, index=True)
    member_id: int = Column(Integer, ForeignKey("members.id"), nullable=False)
    trainer_id: int = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    goal: str = Column(String(256))
    weekly_schedule_json: str = Column(Text, default="{}")
    notes: str = Column(Text, default="")

    member = relationship("Member", back_populates="plans")
    trainer = relationship("Trainer", back_populates="plans")
