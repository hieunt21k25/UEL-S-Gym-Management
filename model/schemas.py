"""Pydantic schemas for request / response validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator

from model.models import (
    DurationUnit, GenderEnum, InvoiceStatus, MemberStatus,
    PaymentMethod, SubStatus, UserRole,
)


# ── Auth ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.staff


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Members ────────────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: EmailStr
    dob: Optional[date] = None
    gender: GenderEnum = GenderEnum.other
    join_date: Optional[date] = None
    status: MemberStatus = MemberStatus.active


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[date] = None
    gender: Optional[GenderEnum] = None
    join_date: Optional[date] = None
    status: Optional[MemberStatus] = None


class MemberRead(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    email: str
    dob: Optional[date]
    gender: GenderEnum
    join_date: Optional[date]
    status: MemberStatus

    model_config = {"from_attributes": True}


# ── Packages ───────────────────────────────────────────────────────────────────

class PackageCreate(BaseModel):
    name: str
    duration_unit: DurationUnit
    duration_value: int
    price: float
    description: Optional[str] = ""


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    duration_unit: Optional[DurationUnit] = None
    duration_value: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None


class PackageRead(BaseModel):
    id: int
    name: str
    duration_unit: DurationUnit
    duration_value: int
    price: float
    description: Optional[str]

    model_config = {"from_attributes": True}


# ── Subscriptions ──────────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    member_id: int
    package_id: int
    start_date: date
    end_date: Optional[date] = None  # computed if not given


class SubscriptionUpdate(BaseModel):
    status: Optional[SubStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SubscriptionRead(BaseModel):
    id: int
    member_id: int
    package_id: int
    start_date: date
    end_date: date
    status: SubStatus

    model_config = {"from_attributes": True}


# ── Check-ins ─────────────────────────────────────────────────────────────────

class CheckInCreate(BaseModel):
    member_id: int
    timestamp: Optional[datetime] = None


class CheckInRead(BaseModel):
    id: int
    member_id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class CheckInStats(BaseModel):
    daily: int
    weekly: int
    monthly: int


# ── Payments & Invoices ────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    member_id: int
    amount: float
    method: PaymentMethod = PaymentMethod.cash
    date: Optional[date] = None
    note: Optional[str] = ""
    related_subscription_id: Optional[int] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    method: Optional[PaymentMethod] = None
    date: Optional[date] = None
    note: Optional[str] = None


class PaymentRead(BaseModel):
    id: int
    member_id: int
    amount: float
    method: PaymentMethod
    date: Optional[date]
    note: Optional[str]
    related_subscription_id: Optional[int]

    model_config = {"from_attributes": True}


class InvoiceRead(BaseModel):
    id: int
    invoice_no: str
    payment_id: int
    member_name: str
    package_name: str
    total: float
    status: InvoiceStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Trainers ───────────────────────────────────────────────────────────────────

class TrainerCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    availability_schedule: Optional[str] = ""


class TrainerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    availability_schedule: Optional[str] = None


class TrainerRead(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    specialty: Optional[str]
    availability_schedule: Optional[str]

    model_config = {"from_attributes": True}


# ── Training Plans ─────────────────────────────────────────────────────────────

class PlanCreate(BaseModel):
    member_id: int
    trainer_id: int
    goal: Optional[str] = ""
    weekly_schedule_json: Optional[str] = "{}"
    notes: Optional[str] = ""


class PlanUpdate(BaseModel):
    goal: Optional[str] = None
    weekly_schedule_json: Optional[str] = None
    notes: Optional[str] = None


class PlanRead(BaseModel):
    id: int
    member_id: int
    trainer_id: int
    goal: Optional[str]
    weekly_schedule_json: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}


# ── Dashboard / Reports ────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_active_members: int
    active_subscriptions: int
    expired_subscriptions: int
    today_checkins: int
    total_revenue: float


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float


class TopMember(BaseModel):
    member_id: int
    full_name: str
    checkin_count: int
