"""Local JSON storage for per-profile reminders and routines on the Pi."""

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
CALENDAR_CACHE_FILE = DATA_DIR / "calendar_caches.json"

_lock = threading.Lock()

DEFAULT_PROFILE_BUCKET: dict[str, Any] = {
    "reminders": [],
    "routines": [],
}

DEFAULT_DATA: dict[str, Any] = {
    "profiles": {
        "toby": deepcopy(DEFAULT_PROFILE_BUCKET),
        "guest": deepcopy(DEFAULT_PROFILE_BUCKET),
    },
    "fired": [],
}

DEFAULT_PROFILE_CONFIG: dict[str, Any] = {
    "displayName": "Toby",
    "calendar": {
        "enabled": False,
        "icsUrl": "",
        "syncMinutes": 15,
        "lookaheadDays": 14,
    },
}

DEFAULT_CONFIG: dict[str, Any] = {
    "defaultProfileId": "toby",
    "guestProfileId": "guest",
    "profiles": {
        "toby": deepcopy(DEFAULT_PROFILE_CONFIG),
        "guest": {
            "displayName": "friend",
            "calendar": deepcopy(DEFAULT_PROFILE_CONFIG["calendar"]),
        },
    },
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


def _migrate_data(data: dict[str, Any]) -> dict[str, Any]:
    if "profiles" in data and isinstance(data["profiles"], dict):
        return data

    profiles = deepcopy(DEFAULT_DATA["profiles"])
    default_id = "toby"

    if data.get("reminders") or data.get("routines"):
        profiles[default_id] = {
            "reminders": list(data.get("reminders", [])),
            "routines": list(data.get("routines", [])),
        }

    return {
        "profiles": profiles,
        "fired": list(data.get("fired", [])),
    }


def _migrate_config(config: dict[str, Any]) -> dict[str, Any]:
    if "profiles" in config and isinstance(config["profiles"], dict):
        return config

    migrated = deepcopy(DEFAULT_CONFIG)
    legacy_calendar = config.get("calendar", {})
    legacy_name = str(config.get("displayName", "Toby"))
    default_id = migrated["defaultProfileId"]

    migrated["profiles"][default_id] = {
        "displayName": legacy_name,
        "calendar": {
            **deepcopy(DEFAULT_PROFILE_CONFIG["calendar"]),
            **(legacy_calendar if isinstance(legacy_calendar, dict) else {}),
        },
    }
    return migrated


def load_data() -> dict[str, Any]:
    with _lock:
        raw = _read_json(DATA_FILE, DEFAULT_DATA)
        data = _migrate_data(raw)

        for profile_id, bucket in data.get("profiles", {}).items():
            if not isinstance(bucket, dict):
                data["profiles"][profile_id] = deepcopy(DEFAULT_PROFILE_BUCKET)
                continue
            for key in ("reminders", "routines"):
                if key not in bucket or not isinstance(bucket[key], list):
                    bucket[key] = []

        if "fired" not in data or not isinstance(data["fired"], list):
            data["fired"] = []

        if raw != data:
            _write_json(DATA_FILE, data)

        return data


def save_data(data: dict[str, Any]) -> None:
    with _lock:
        _write_json(DATA_FILE, data)


def load_config() -> dict[str, Any]:
    with _lock:
        raw = _read_json(CONFIG_FILE, DEFAULT_CONFIG)
        config = _migrate_config(raw)

        if raw != config:
            _write_json(CONFIG_FILE, config)

        return config


def save_config(config: dict[str, Any]) -> None:
    with _lock:
        _write_json(CONFIG_FILE, config)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def ensure_profile(profile_id: str, display_name: str | None = None) -> None:
    data = load_data()
    config = load_config()

    bucket = data["profiles"].setdefault(profile_id, deepcopy(DEFAULT_PROFILE_BUCKET))
    for key in ("reminders", "routines"):
        if key not in bucket:
            bucket[key] = []

    profile_config = config["profiles"].setdefault(profile_id, deepcopy(DEFAULT_PROFILE_CONFIG))
    if display_name:
        profile_config["displayName"] = display_name
    if "calendar" not in profile_config:
        profile_config["calendar"] = deepcopy(DEFAULT_PROFILE_CONFIG["calendar"])

    save_data(data)
    save_config(config)


def get_profile_bucket(profile_id: str) -> dict[str, Any]:
    data = load_data()
    return data["profiles"].setdefault(profile_id, deepcopy(DEFAULT_PROFILE_BUCKET))


def get_profile_config(profile_id: str) -> dict[str, Any]:
    config = load_config()
    profiles = config.setdefault("profiles", {})
    return profiles.setdefault(profile_id, deepcopy(DEFAULT_PROFILE_CONFIG))


def get_display_name(profile_id: str) -> str:
    return str(get_profile_config(profile_id).get("displayName", profile_id))


def list_profile_ids() -> list[str]:
    data = load_data()
    config = load_config()
    ids = set(data.get("profiles", {}).keys()) | set(config.get("profiles", {}).keys())
    return sorted(ids)


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


def load_calendar_caches() -> dict[str, Any]:
    with _lock:
        raw = _read_json(CALENDAR_CACHE_FILE, {"profiles": {}})
        if "profiles" not in raw:
            legacy = raw if isinstance(raw, dict) else {}
            raw = {"profiles": {"toby": legacy}}
        return raw


def save_calendar_caches(payload: dict[str, Any]) -> None:
    with _lock:
        _write_json(CALENDAR_CACHE_FILE, payload)


def get_calendar_cache(profile_id: str) -> dict[str, Any]:
    caches = load_calendar_caches()
    profile_cache = caches.get("profiles", {}).get(profile_id)
    if isinstance(profile_cache, dict):
        return profile_cache
    return {"syncedAt": None, "events": [], "error": None}


def set_calendar_cache(profile_id: str, cache: dict[str, Any]) -> None:
    caches = load_calendar_caches()
    profiles = caches.setdefault("profiles", {})
    profiles[profile_id] = cache
    save_calendar_caches(caches)
