"""
ui/api_client.py
────────────────
Centralised HTTP client. All API calls live here — pages never call requests directly.
Singleton: from ui.api_client import client
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

BASE_URL   = "http://127.0.0.1:8000"
TOKEN_FILE = Path(__file__).resolve().parent.parent / ".session_token.json"


class ApiClient:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url  = base_url
        self._token    = ""
        self._role     = ""
        self._username = ""

    # ── Token ──────────────────────────────────────────────────────────────────

    def set_token(self, token: str, role: str, username: str) -> None:
        self._token = token; self._role = role; self._username = username
        try: TOKEN_FILE.write_text(json.dumps({"token": token, "role": role, "username": username}))
        except Exception: pass

    def load_token(self) -> bool:
        try:
            d = json.loads(TOKEN_FILE.read_text())
            self._token = d.get("token", ""); self._role = d.get("role", ""); self._username = d.get("username", "")
            return bool(self._token)
        except Exception: return False

    def clear_token(self) -> None:
        self._token = self._role = self._username = ""
        try: TOKEN_FILE.unlink(missing_ok=True)
        except Exception: pass

    @property
    def token(self) -> str:     return self._token
    @property
    def role(self) -> str:      return self._role
    @property
    def username(self) -> str:  return self._username
    @property
    def is_admin(self) -> bool: return self._role == "admin"

    # ── HTTP ───────────────────────────────────────────────────────────────────

    def _h(self)                -> dict: return {"Authorization": f"Bearer {self._token}"} if self._token else {}
    def _url(self, p: str)      -> str:  return f"{self.base_url}{p}"

    def _get(self, p, params=None) -> Any:
        r = requests.get(self._url(p), headers=self._h(), params=params, timeout=10); r.raise_for_status(); return r.json()

    def _post(self, p, data=None) -> Any:
        r = requests.post(self._url(p), headers=self._h(), json=data or {}, timeout=10); r.raise_for_status(); return r.json()

    def _put(self, p, data) -> Any:
        r = requests.put(self._url(p), headers=self._h(), json=data, timeout=10); r.raise_for_status(); return r.json()

    def _delete(self, p) -> None:
        r = requests.delete(self._url(p), headers=self._h(), timeout=10); r.raise_for_status()

    def _download(self, p) -> bytes:
        r = requests.get(self._url(p), headers=self._h(), timeout=20); r.raise_for_status(); return r.content

    def is_alive(self) -> bool:
        try: requests.get(self._url("/"), timeout=3); return True
        except: return False

    # ── Auth ───────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> dict:
        d = self._post("/auth/login", {"username": username, "password": password})
        self.set_token(d["access_token"], d["role"], d["username"]); return d

    def register(self, username: str, email: str, password: str, role: str = "staff") -> dict:
        return self._post("/auth/register", {"username": username, "email": email, "password": password, "role": role})

    def get_me(self) -> dict: return self._get("/auth/me")

    def verify_token(self) -> bool:
        try: self.get_me(); return True
        except: return False

    # ── Members ────────────────────────────────────────────────────────────────

    def get_members(self, status=None, search=None, join_date_from=None, join_date_to=None) -> List[dict]:
        p = {}
        if status:         p["status"] = status
        if search:         p["search"] = search
        if join_date_from: p["join_date_from"] = join_date_from
        if join_date_to:   p["join_date_to"]   = join_date_to
        return self._get("/members", p)

    def get_member(self, mid: int) -> dict:  return self._get(f"/members/{mid}")
    def create_member(self, d) -> dict:      return self._post("/members", d)
    def update_member(self, mid, d) -> dict: return self._put(f"/members/{mid}", d)
    def delete_member(self, mid) -> None:    self._delete(f"/members/{mid}")

    # ── Packages ───────────────────────────────────────────────────────────────

    def get_packages(self) -> List[dict]:          return self._get("/packages")
    def create_package(self, d) -> dict:           return self._post("/packages", d)
    def update_package(self, pid, d) -> dict:      return self._put(f"/packages/{pid}", d)
    def delete_package(self, pid) -> None:         self._delete(f"/packages/{pid}")

    # ── Subscriptions ──────────────────────────────────────────────────────────

    def get_subscriptions(self, member_id=None) -> List[dict]:
        return self._get("/subscriptions", {"member_id": member_id} if member_id else {})
    def create_subscription(self, d) -> dict:          return self._post("/subscriptions", d)
    def update_subscription(self, sid, d) -> dict:     return self._put(f"/subscriptions/{sid}", d)
    def refresh_expired(self) -> dict:                 return self._post("/subscriptions/refresh_expired")

    # ── Check-ins ─────────────────────────────────────────────────────────────

    def get_checkins(self, member_id=None) -> List[dict]:
        return self._get("/checkins", {"member_id": member_id} if member_id else {})
    def create_checkin(self, member_id: int) -> dict:  return self._post("/checkins", {"member_id": member_id})
    def get_checkin_stats(self) -> dict:               return self._get("/checkins/stats")

    # ── Payments ───────────────────────────────────────────────────────────────

    def get_payments(self, member_id=None) -> List[dict]:
        return self._get("/payments", {"member_id": member_id} if member_id else {})
    def create_payment(self, d) -> dict:           return self._post("/payments", d)
    def update_payment(self, pid, d) -> dict:      return self._put(f"/payments/{pid}", d)
    def delete_payment(self, pid) -> None:         self._delete(f"/payments/{pid}")
    def generate_invoice(self, pid) -> dict:       return self._post(f"/payments/{pid}/invoice")

    # ── Trainers ───────────────────────────────────────────────────────────────

    def get_trainers(self) -> List[dict]:           return self._get("/trainers")
    def create_trainer(self, d) -> dict:            return self._post("/trainers", d)
    def update_trainer(self, tid, d) -> dict:       return self._put(f"/trainers/{tid}", d)
    def delete_trainer(self, tid) -> None:          self._delete(f"/trainers/{tid}")

    # ── Plans ──────────────────────────────────────────────────────────────────

    def get_plans(self, member_id=None) -> List[dict]:
        return self._get("/plans", {"member_id": member_id} if member_id else {})
    def create_plan(self, d) -> dict:              return self._post("/plans", d)
    def update_plan(self, pid, d) -> dict:         return self._put(f"/plans/{pid}", d)
    def delete_plan(self, pid) -> None:            self._delete(f"/plans/{pid}")

    # ── Reports ────────────────────────────────────────────────────────────────

    def get_dashboard(self) -> dict:               return self._get("/reports/dashboard")
    def get_revenue_monthly(self) -> List[dict]:   return self._get("/reports/revenue_monthly")
    def get_top_checkins(self) -> List[dict]:      return self._get("/reports/top_checkins")

    # ── Export ─────────────────────────────────────────────────────────────────

    def export_payments_csv(self) -> bytes:        return self._download("/export/payments.csv")
    def export_checkins_csv(self) -> bytes:        return self._download("/export/checkins.csv")


# ── Singleton ─────────────────────────────────────────────────────────────────
client = ApiClient()
