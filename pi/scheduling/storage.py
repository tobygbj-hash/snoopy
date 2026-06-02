"""Local JSON storage for reminders and routines on the Pi."""

from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("SNOOPY_SCHEDULING_DIR", Path.home() / ".config" / "snoopy"))
DATA_FILE = DATA_DIR / "scheduling.json"
CONFIG_FILE = DATA_DIR / "config.json"

_lock = threading.Lock()

DEFAULT_DATA: dict[str, Any] = {
    "reminders": [],
    "routines": [],
    "fired": [],
}

DEFAULT_CONFIG: dict[str, Any] = {
    "calendar": {
        "enabled": False,
        "icsUrl": "",
        "syncMinutes": 15,
        "lookaheadDays": 14,
    },
    "displayName": "Toby",
}


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return deepcopy(default)

    try:
        with path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return deepcopy(default)

    if not isinstance(loaded, dict):
        return deepcopy(default)

    return loaded


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_dir()
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp.replace(path)


def load_data() -> dict[str, Any]:
    with _lock:
        data = _read_json(DATA_FILE, DEFAULT_DATA)
        for key in ("reminders", "routines", "fired"):
            if key not in data or not isinstance(data[key], list):
                data[key] = []
        return data


def save_data(data: dict[str, Any]) -> None:
    with _lock:
        _write_json(DATA_FILE, data)


def load_config() -> dict[str, Any]:
    with _lock:
        config = _read_json(CONFIG_FILE, DEFAULT_CONFIG)
        if "calendar" not in config or not isinstance(config["calendar"], dict):
            config["calendar"] = deepcopy(DEFAULT_CONFIG["calendar"])
        if "displayName" not in config:
            config["displayName"] = DEFAULT_CONFIG["displayName"]
        return config


def save_config(config: dict[str, Any]) -> None:
    with _lock:
        _write_json(CONFIG_FILE, config)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def prune_fired(data: dict[str, Any], keep_days: int = 3) -> None:
    cutoff = datetime.now().date().toordinal() - keep_days
    kept = []

    for entry in data.get("fired", []):
        if not isinstance(entry, dict):
            continue

        try:
            fired_on = date.fromisoformat(str(entry.get("date", ""))).toordinal()
        except ValueError:
            continue

        if fired_on >= cutoff:
            kept.append(entry)

    data["fired"] = kept
