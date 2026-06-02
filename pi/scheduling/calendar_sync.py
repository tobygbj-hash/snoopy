"""Sync calendar events from a private ICS URL (Google / iCloud / Outlook feeds)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from storage import DATA_DIR, load_config

CACHE_FILE = DATA_DIR / "calendar_cache.json"
_lock = threading.Lock()


def _cache_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_FILE


def load_calendar_cache() -> dict:
    path = _cache_path()

    if not path.exists():
        return {"syncedAt": None, "events": [], "error": None}

    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"syncedAt": None, "events": [], "error": "cache_read_failed"}


def save_calendar_cache(payload: dict) -> None:
    with _lock:
        path = _cache_path()
        temp = path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        temp.replace(path)


def _parse_ics_datetime(value: str) -> datetime | None:
    raw = value.strip()

    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    try:
        return datetime.strptime(raw[:8], "%Y%m%d").replace(hour=9, minute=0)
    except ValueError:
        return None


def parse_ics(text: str, lookahead_days: int) -> list[dict]:
    events: list[dict] = []
    now = datetime.now()
    horizon = now + timedelta(days=lookahead_days)
    blocks = text.split("BEGIN:VEVENT")

    for block in blocks[1:]:
        if "END:VEVENT" not in block:
            continue

        summary = ""
        dtstart = ""
        uid = ""

        for line in block.splitlines():
            if line.startswith("SUMMARY"):
                summary = line.split(":", 1)[-1].strip()
            elif line.startswith("DTSTART"):
                dtstart = line.split(":", 1)[-1].strip()
            elif line.startswith("UID"):
                uid = line.split(":", 1)[-1].strip()

        if not dtstart:
            continue

        start = _parse_ics_datetime(dtstart)
        if not start or start < now - timedelta(minutes=2) or start > horizon:
            continue

        safe_summary = " ".join(summary.split())[:120]
        events.append(
            {
                "id": uid or f"ics-{start.isoformat()}",
                "summary": safe_summary or "Calendar event",
                "start": start.isoformat(),
                "source": "calendar",
            }
        )

    events.sort(key=lambda item: item["start"])
    return events


def sync_calendar(force: bool = False) -> dict:
    config = load_config()
    calendar = config.get("calendar", {})
    enabled = bool(calendar.get("enabled"))
    ics_url = str(calendar.get("icsUrl", "")).strip()
    lookahead_days = int(calendar.get("lookaheadDays", 14) or 14)

    if not enabled or not ics_url:
        payload = {
            "syncedAt": datetime.now().isoformat(),
            "events": [],
            "error": None if not enabled else "missing_ics_url",
            "enabled": enabled,
        }
        save_calendar_cache(payload)
        return payload

    cache = load_calendar_cache()
    sync_minutes = int(calendar.get("syncMinutes", 15) or 15)

    if not force and cache.get("syncedAt"):
        try:
            last = datetime.fromisoformat(cache["syncedAt"])
            if datetime.now() - last < timedelta(minutes=sync_minutes):
                return cache
        except ValueError:
            pass

    try:
        request = urllib.request.Request(
            ics_url,
            headers={"User-Agent": "SnoopyPiScheduler/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        payload = {
            "syncedAt": datetime.now().isoformat(),
            "events": cache.get("events", []),
            "error": str(error)[:200],
            "enabled": True,
        }
        save_calendar_cache(payload)
        return payload

    events = parse_ics(body, lookahead_days)
    payload = {
        "syncedAt": datetime.now().isoformat(),
        "events": events,
        "error": None,
        "enabled": True,
    }
    save_calendar_cache(payload)
    return payload


def events_due_now(cache: dict, window_minutes: int = 1) -> list[dict]:
    due: list[dict] = []
    now = datetime.now()
    start_window = now - timedelta(minutes=window_minutes)

    for event in cache.get("events", []):
        try:
            start = datetime.fromisoformat(event["start"])
        except (KeyError, ValueError):
            continue

        if start_window <= start <= now + timedelta(seconds=30):
            due.append(event)

    return due
