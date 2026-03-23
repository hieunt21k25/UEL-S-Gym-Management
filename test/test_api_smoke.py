"""Smoke tests — spin up the API and check every major route."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _token(username="admin", password="admin123") -> str:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def auth():
    return {"Authorization": f"Bearer {_token()}"}


def test_health():
    resp = client.get("/")
    assert resp.status_code == 200


def test_login_admin():
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_staff():
    resp = client.post("/auth/login", json={"username": "staff", "password": "staff123"})
    assert resp.status_code == 200


def test_invalid_login():
    resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_me(auth):
    resp = client.get("/auth/me", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_list_members(auth):
    resp = client.get("/members", headers=auth)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_member(auth):
    payload = {
        "full_name": "Test User",
        "email": "testuser_smoke@gym.com",
        "phone": "555-9999",
        "gender": "male",
        "status": "active",
    }
    resp = client.post("/members", json=payload, headers=auth)
    assert resp.status_code == 201
    assert resp.json()["full_name"] == "Test User"


def test_list_packages(auth):
    resp = client.get("/packages", headers=auth)
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_list_subscriptions(auth):
    resp = client.get("/subscriptions", headers=auth)
    assert resp.status_code == 200


def test_refresh_expired(auth):
    resp = client.post("/subscriptions/refresh_expired", headers=auth)
    assert resp.status_code == 200


def test_checkin_stats(auth):
    resp = client.get("/checkins/stats", headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "daily" in data


def test_list_payments(auth):
    resp = client.get("/payments", headers=auth)
    assert resp.status_code == 200


def test_list_trainers(auth):
    resp = client.get("/trainers", headers=auth)
    assert resp.status_code == 200


def test_list_plans(auth):
    resp = client.get("/plans", headers=auth)
    assert resp.status_code == 200


def test_dashboard(auth):
    resp = client.get("/reports/dashboard", headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_active_members" in data


def test_revenue_monthly(auth):
    resp = client.get("/reports/revenue_monthly", headers=auth)
    assert resp.status_code == 200


def test_top_checkins(auth):
    resp = client.get("/reports/top_checkins", headers=auth)
    assert resp.status_code == 200


def test_export_payments_csv(auth):
    resp = client.get("/export/payments.csv", headers=auth)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_export_checkins_csv(auth):
    resp = client.get("/export/checkins.csv", headers=auth)
    assert resp.status_code == 200


def test_staff_cannot_create_package():
    staff_token = _token("staff", "staff123")
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/packages",
        json={"name": "Hack", "duration_unit": "months", "duration_value": 1, "price": 1.0},
        headers=headers,
    )
    assert resp.status_code == 403
