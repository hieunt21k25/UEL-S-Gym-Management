"""Local token storage — persists JWT to a plain file for session continuity."""

from __future__ import annotations

import json
from pathlib import Path

_TOKEN_FILE = Path(__file__).parent.parent / ".session_token.json"

_session: dict = {}


def save_token(token: str, role: str, username: str) -> None:
    """Persist token + metadata to disk."""
    global _session
    _session = {"token": token, "role": role, "username": username}
    try:
        _TOKEN_FILE.write_text(json.dumps(_session))
    except Exception:
        pass


def load_token() -> dict:
    """Load token from disk (used for auto-login)."""
    global _session
    try:
        _session = json.loads(_TOKEN_FILE.read_text())
    except Exception:
        _session = {}
    return _session


def get_token() -> str:
    """Return current in-memory token."""
    return _session.get("token", "")


def get_role() -> str:
    return _session.get("role", "")


def get_username() -> str:
    return _session.get("username", "")


def clear_token() -> None:
    """Log out: clear memory and disk token."""
    global _session
    _session = {}
    try:
        _TOKEN_FILE.unlink(missing_ok=True)
    except Exception:
        pass
