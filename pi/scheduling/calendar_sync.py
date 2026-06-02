"""Per-profile calendar sync from private ICS URLs."""

from __future__ import annotations

import urllib.error
import urllib.request
from datetime import datetime, timedelta

from storage import get_profile_config, get_calendar_cache, set_calendar_cache


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
                "profileId": None,
            }
        )

    events.sort(key=lambda item: item["start"])
    return events


def sync_calendar(profile_id: str, force: bool = False) -> dict:
    profile_config = get_profile_config(profile_id)
    calendar = profile_config.get("calendar", {})
    enabled = bool(calendar.get("enabled"))
    ics_url = str(calendar.get("icsUrl", "")).strip()
    lookahead_days = int(calendar.get("lookaheadDays", 14) or 14)

    if not enabled or not ics_url:
        payload = {
            "syncedAt": datetime.now().isoformat(),
            "events": [],
            "error": None if not enabled else "missing_ics_url",
            "enabled": enabled,
            "profileId": profile_id,
        }
        set_calendar_cache(profile_id, payload)
        return payload

    cache = get_calendar_cache(profile_id)
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
            "profileId": profile_id,
        }
        set_calendar_cache(profile_id, payload)
        return payload

    events = parse_ics(body, lookahead_days)
    for event in events:
        event["profileId"] = profile_id

    payload = {
        "syncedAt": datetime.now().isoformat(),
        "events": events,
        "error": None,
        "enabled": True,
        "profileId": profile_id,
    }
    set_calendar_cache(profile_id, payload)
    return payload


def sync_all_calendars(force: bool = False) -> None:
    from storage import list_profile_ids

    for profile_id in list_profile_ids():
        sync_calendar(profile_id, force=force)


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
