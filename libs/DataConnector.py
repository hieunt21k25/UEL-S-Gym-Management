"""
libs/DataConnector.py
─────────────────────
All data access for the JSON-based Gym Manager app.
Reads/writes dataset/*.json via JsonFileFactory.
Also handles login(), register(), and auto-expire subscriptions.
"""
from __future__ import annotations
from datetime import date, datetime
from pathlib import Path

from libs.FileFactory import JsonFileFactory
from model.User         import User
from model.Member       import Member
from model.Package      import Package
from model.Subscription import Subscription
from model.CheckIn      import CheckIn
from model.Payment      import Payment
from model.Trainer      import Trainer
from model.Plan         import Plan

_DS = Path(__file__).resolve().parent.parent / "dataset"


class DataConnector:
    def _p(self, f): return str(_DS / f)

    # ── Auth ──────────────────────────────────────────────────────────────────

    def get_all_users(self) -> list[User]:
        return JsonFileFactory().read_data(self._p("users.json"), User)

    def save_users(self, users: list[User]) -> bool:
        return JsonFileFactory().write_data(users, self._p("users.json"))

    def login(self, username: str, password: str) -> User | None:
        for u in self.get_all_users():
            if u.username == username and u.password == password:
                return u
        return None

    def register(self, username: str, email: str, password: str, role: str) -> User | None:
        users = self.get_all_users()
        if any(u.username == username for u in users):
            return None   # duplicate
        new_id = f"U{str(len(users) + 1).zfill(3)}"
        user = User(user_id=new_id, username=username, email=email,
                    password=password, role=role)
        users.append(user)
        self.save_users(users)
        return user

    # ── Members ───────────────────────────────────────────────────────────────

    def get_all_members(self, status=None, search=None) -> list[Member]:
        members = JsonFileFactory().read_data(self._p("members.json"), Member)
        if status:
            members = [m for m in members if m.status == status]
        if search:
            s = search.lower()
            members = [m for m in members
                       if s in m.full_name.lower() or s in m.phone or s in m.email.lower()]
        return members

    def save_members(self, members: list[Member]) -> bool:
        return JsonFileFactory().write_data(members, self._p("members.json"))

    def next_member_id(self) -> str:
        members = self.get_all_members()
        return f"M{str(len(members) + 1).zfill(3)}"

    # ── Packages ──────────────────────────────────────────────────────────────

    def get_all_packages(self) -> list[Package]:
        return JsonFileFactory().read_data(self._p("packages.json"), Package)

    def save_packages(self, packages: list[Package]) -> bool:
        return JsonFileFactory().write_data(packages, self._p("packages.json"))

    def next_package_id(self) -> str:
        pkgs = self.get_all_packages()
        return f"P{str(len(pkgs) + 1).zfill(3)}"

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def get_all_subscriptions(self, member_id=None) -> list[Subscription]:
        subs = JsonFileFactory().read_data(self._p("subscriptions.json"), Subscription)
        if member_id:
            subs = [s for s in subs if s.member_id == member_id]
        return subs

    def save_subscriptions(self, subs: list[Subscription]) -> bool:
        return JsonFileFactory().write_data(subs, self._p("subscriptions.json"))

    def next_sub_id(self) -> str:
        subs = self.get_all_subscriptions()
        return f"S{str(len(subs) + 1).zfill(3)}"

    def auto_expire_subscriptions(self) -> int:
        """Mark subscriptions past end_date as expired. Returns count changed."""
        subs    = self.get_all_subscriptions()
        today   = date.today().isoformat()
        changed = 0
        for s in subs:
            if s.status == "active" and s.end_date < today:
                s.status = "expired"
                changed += 1
        if changed:
            self.save_subscriptions(subs)
        return changed

    def has_active_subscription(self, member_id: str) -> bool:
        today = date.today().isoformat()
        return any(
            s.member_id == member_id and s.status == "active" and s.end_date >= today
            for s in self.get_all_subscriptions()
        )

    # ── Check-ins ─────────────────────────────────────────────────────────────

    def get_all_checkins(self, member_id=None) -> list[CheckIn]:
        cis = JsonFileFactory().read_data(self._p("checkins.json"), CheckIn)
        if member_id:
            cis = [c for c in cis if c.member_id == member_id]
        return cis

    def save_checkins(self, checkins: list[CheckIn]) -> bool:
        return JsonFileFactory().write_data(checkins, self._p("checkins.json"))

    def checkin_member(self, member_id: str) -> tuple[bool, str]:
        """Returns (success, message)."""
        if not self.has_active_subscription(member_id):
            return False, "No active subscription."
        cis    = self.get_all_checkins()
        new_id = f"CI{str(len(cis) + 1).zfill(4)}"
        ts     = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        cis.append(CheckIn(checkin_id=new_id, member_id=member_id, timestamp=ts))
        self.save_checkins(cis)
        return True, f"Check-in recorded at {ts}"

    def get_checkin_stats(self) -> dict:
        cis = self.get_all_checkins()
        today = date.today()
        td = today.isoformat()
        wk = (today.isocalendar().week, today.year)
        mo = (today.month, today.year)
        return {
            "today":   sum(1 for c in cis if c.timestamp[:10] == td),
            "weekly":  sum(1 for c in cis
                           if datetime.fromisoformat(c.timestamp).isocalendar()[:2] == wk[::-1]),
            "monthly": sum(1 for c in cis
                           if (datetime.fromisoformat(c.timestamp).month,
                               datetime.fromisoformat(c.timestamp).year) == mo),
            "total":   len(cis),
        }

    # ── Payments ──────────────────────────────────────────────────────────────

    def get_all_payments(self, member_id=None) -> list[Payment]:
        pays = JsonFileFactory().read_data(self._p("payments.json"), Payment)
        if member_id:
            pays = [p for p in pays if p.member_id == member_id]
        return pays

    def save_payments(self, payments: list[Payment]) -> bool:
        return JsonFileFactory().write_data(payments, self._p("payments.json"))

    def next_payment_id(self) -> str:
        pays = self.get_all_payments()
        return f"PAY{str(len(pays) + 1).zfill(4)}"

    def monthly_revenue(self) -> list[dict]:
        pays = self.get_all_payments()
        rev: dict[str, float] = {}
        for p in pays:
            key = p.date[:7]  # YYYY-MM
            rev[key] = rev.get(key, 0) + float(p.amount)
        return [{"month": k, "revenue": v} for k, v in sorted(rev.items())]

    # ── Trainers ──────────────────────────────────────────────────────────────

    def get_all_trainers(self) -> list[Trainer]:
        return JsonFileFactory().read_data(self._p("trainers.json"), Trainer)

    def save_trainers(self, trainers: list[Trainer]) -> bool:
        return JsonFileFactory().write_data(trainers, self._p("trainers.json"))

    def next_trainer_id(self) -> str:
        ts = self.get_all_trainers()
        return f"T{str(len(ts) + 1).zfill(3)}"

    # ── Plans ─────────────────────────────────────────────────────────────────

    def get_all_plans(self, member_id=None) -> list[Plan]:
        plans = JsonFileFactory().read_data(self._p("plans.json"), Plan)
        if member_id:
            plans = [p for p in plans if p.member_id == member_id]
        return plans

    def save_plans(self, plans: list[Plan]) -> bool:
        return JsonFileFactory().write_data(plans, self._p("plans.json"))

    def next_plan_id(self) -> str:
        plans = self.get_all_plans()
        return f"PL{str(len(plans) + 1).zfill(3)}"

    # ── Dashboard stats ───────────────────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        members  = self.get_all_members()
        subs     = self.get_all_subscriptions()
        today    = date.today().isoformat()
        
        # New members
        today_ymd = datetime.now().strftime("%Y-%m-%d")
        mo_prefix = datetime.now().strftime("%Y-%m-")
        new_m_today = sum(1 for m in members if getattr(m, 'date_joined', '') == today_ymd)
        new_m_month = sum(1 for m in members if getattr(m, 'date_joined', '').startswith(mo_prefix))

        active_m = sum(1 for m in members if m.status == "active")
        active_s = sum(1 for s in subs if s.status == "active")
        expired_s= sum(1 for s in subs if s.status == "expired")
        ci_stats = self.get_checkin_stats()
        revenue  = self.monthly_revenue()
        total_rev = sum([r.get('revenue', 0.0) for r in revenue])

        return {
            "total_members":        len(members),
            "new_members_today":    new_m_today,
            "new_members_month":    new_m_month,
            "active_members":       active_m,
            "active_subscriptions": active_s,
            "expired_subscriptions":expired_s,
            "today_checkins":       ci_stats["today"],
            "monthly_checkins":     ci_stats["monthly"],
            "total_revenue":        total_rev,
            "monthly_revenue":      revenue,
        }
