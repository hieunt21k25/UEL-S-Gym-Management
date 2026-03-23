"""
libs/data_loader.py
───────────────────
Reusable helpers to load JSON dataset files.

Usage:
    from libs.data_loader import load_json, dataset_path

    users = load_json("users.json")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

# Always resolve relative to project root (two levels up from libs/)
_DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"


def dataset_path(filename: str) -> Path:
    """Return absolute path to a file inside dataset/."""
    return _DATASET_DIR / filename


def load_json(filename: str) -> List[Any]:
    """
    Load a JSON file from the dataset/ directory.

    Args:
        filename: file name relative to dataset/ (e.g. "members.json")

    Returns:
        Parsed Python object (list or dict).

    Raises:
        FileNotFoundError: if the file doesn't exist.
        ValueError: if the file contains invalid JSON.
    """
    path = dataset_path(filename)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {path}\n"
            f"Expected location: dataset/{filename}"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc


def validate_required(record: dict, fields: list[str], source: str) -> None:
    """Raise ValueError if any required field is missing from a record."""
    missing = [f for f in fields if f not in record]
    if missing:
        raise ValueError(
            f"[{source}] Record missing required fields {missing}: {record}"
        )
