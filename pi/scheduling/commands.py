"""Apply scheduling commands with per-profile isolation."""

from __future__ import annotations

from datetime import datetime

from calendar_sync import sync_calendar
from parse_voice import parse_command, parse_time_token
from profiles import resolve_profile
from storage import (
    ensure_profile,
    get_display_name,
    get_profile_bucket,
    load_config,
    load_data,
    new_id,
    save_config,
    save_data,
)


def _with_profile(payload: dict) -> tuple[str, str]:
    identify = bool(payload.get("identify", True))
    profile_id, display_name = resolve_profile(payload, identify=identify)
    ensure_profile(profile_id, display_name)
    return profile_id, display_name


def _normalize_time(value: str) -> str:
    parsed = parse_time_token(str(value))
    return parsed or str(value)


def add_reminder(payload: dict) -> dict:
    profile_id, display_name = _with_profile(payload)
    data = load_data()
    bucket = data["profiles"][profile_id]

    entry = {
        "id": new_id(),
        "profileId": profile_id,
        "time": _normalize_time(payload["time"]),
        "date": payload.get("date"),
        "message": payload["message"],
        "repeat": payload.get("repeat"),
        "enabled": True,
        "createdAt": datetime.now().isoformat(),
    }
    bucket["reminders"].append(entry)
    save_data(data)
    entry["displayName"] = display_name
    return entry


def add_routine(payload: dict) -> dict:
    profile_id, display_name = _with_profile(payload)
    data = load_data()
    bucket = data["profiles"][profile_id]

    entry = {
        "id": new_id(),
        "profileId": profile_id,
        "time": _normalize_time(payload["time"]),
        "message": payload["message"],
        "days": payload.get("days", list(range(7))),
        "enabled": True,
        "createdAt": datetime.now().isoformat(),
    }
    bucket["routines"].append(entry)
    save_data(data)
    entry["displayName"] = display_name
    return entry


def list_reminders(profile_id: str | None = None) -> list[dict]:
    data = load_data()

    if profile_id:
        bucket = data["profiles"].get(profile_id, {})
        return [item for item in bucket.get("reminders", []) if item.get("enabled", True)]

    combined: list[dict] = []
    for pid, bucket in data.get("profiles", {}).items():
        for item in bucket.get("reminders", []):
            if item.get("enabled", True):
                enriched = dict(item)
                enriched.setdefault("profileId", pid)
                combined.append(enriched)
    return combined


def list_routines(profile_id: str | None = None) -> list[dict]:
    data = load_data()

    if profile_id:
        bucket = data["profiles"].get(profile_id, {})
        return [item for item in bucket.get("routines", []) if item.get("enabled", True)]

    combined: list[dict] = []
    for pid, bucket in data.get("profiles", {}).items():
        for item in bucket.get("routines", []):
            if item.get("enabled", True):
                enriched = dict(item)
                enriched.setdefault("profileId", pid)
                combined.append(enriched)
    return combined


def delete_reminder(item_id: str, profile_id: str | None = None) -> bool:
    data = load_data()
    deleted = False

    profile_ids = [profile_id] if profile_id else list(data.get("profiles", {}).keys())

    for pid in profile_ids:
        bucket = data["profiles"].get(pid, {})
        before = len(bucket.get("reminders", []))
        bucket["reminders"] = [
            item for item in bucket.get("reminders", []) if item.get("id") != item_id
        ]
        if len(bucket["reminders"]) < before:
            deleted = True

    save_data(data)
    return deleted


def delete_routine(item_id: str, profile_id: str | None = None) -> bool:
    data = load_data()
    deleted = False

    profile_ids = [profile_id] if profile_id else list(data.get("profiles", {}).keys())

    for pid in profile_ids:
        bucket = data["profiles"].get(pid, {})
        before = len(bucket.get("routines", []))
        bucket["routines"] = [
            item for item in bucket.get("routines", []) if item.get("id") != item_id
        ]
        if len(bucket["routines"]) < before:
            deleted = True

    save_data(data)
    return deleted


def handle_voice(transcript: str, payload: dict | None = None) -> dict:
    payload = dict(payload or {})
    payload.setdefault("identify", True)
    profile_id, display_name = resolve_profile(payload, identify=True)
    ensure_profile(profile_id, display_name)

    parsed = parse_command(transcript)

    if not parsed:
        return {"handled": False, "profileId": profile_id, "displayName": display_name}

    action = parsed.get("action")
    parsed["profileId"] = profile_id
    parsed["displayName"] = display_name
    parsed["identify"] = False

    if action == "add_reminder":
        entry = add_reminder(parsed)
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "reminderSet",
            "entry": entry,
        }

    if action == "add_routine":
        entry = add_routine(parsed)
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "routineSet",
            "entry": entry,
        }

    if action == "list_reminders":
        items = list_reminders(profile_id)
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "reminderListReady" if items else "reminderListEmpty",
            "items": items,
        }

    if action == "list_routines":
        items = list_routines(profile_id)
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "routineListReady" if items else "routineListEmpty",
            "items": items,
        }

    if action == "list_calendar":
        cache = sync_calendar(profile_id, force=True)
        events = cache.get("events", [])
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "calendarListReady" if events else "calendarListEmpty",
            "items": events[:10],
            "calendarError": cache.get("error"),
        }

    if action == "error":
        return {
            "handled": True,
            "profileId": profile_id,
            "displayName": display_name,
            "speechKey": "scheduleError",
            "reason": parsed.get("reason"),
        }

    return {"handled": False, "profileId": profile_id, "displayName": display_name}


def update_calendar_config(payload: dict) -> dict:
    profile_id, display_name = _with_profile(payload)
    config = load_config()
    profile_config = config["profiles"][profile_id]
    calendar = profile_config.setdefault("calendar", {})

    calendar["enabled"] = bool(payload.get("enabled", calendar.get("enabled")))
    if "icsUrl" in payload:
        calendar["icsUrl"] = str(payload.get("icsUrl", "")).strip()
    if "syncMinutes" in payload:
        calendar["syncMinutes"] = int(payload.get("syncMinutes", 15))
    if "lookaheadDays" in payload:
        calendar["lookaheadDays"] = int(payload.get("lookaheadDays", 14))

    profile_config["displayName"] = display_name
    save_config(config)
    sync_calendar(profile_id, force=True)
    return {
        "profileId": profile_id,
        "displayName": display_name,
        "calendar": calendar,
    }


def get_schedule_snapshot(profile_id: str | None = None) -> dict:
    from storage import get_calendar_cache, load_config

    if profile_id:
        return {
            "profileId": profile_id,
            "displayName": get_display_name(profile_id),
            "reminders": list_reminders(profile_id),
            "routines": list_routines(profile_id),
            "calendar": get_calendar_cache(profile_id),
            "config": load_config(),
        }

    profiles: dict[str, dict] = {}
    for pid in load_data().get("profiles", {}):
        profiles[pid] = {
            "displayName": get_display_name(pid),
            "reminders": list_reminders(pid),
            "routines": list_routines(pid),
            "calendar": get_calendar_cache(pid),
        }

    return {"profiles": profiles, "config": load_config()}
