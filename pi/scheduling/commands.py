"""Apply scheduling commands from voice or HTTP."""

from __future__ import annotations

from datetime import datetime

from parse_voice import parse_command
from storage import load_data, load_config, new_id, save_data, save_config
from calendar_sync import sync_calendar


def add_reminder(payload: dict) -> dict:
    data = load_data()
    entry = {
        "id": new_id(),
        "time": payload["time"],
        "date": payload.get("date"),
        "message": payload["message"],
        "repeat": payload.get("repeat"),
        "enabled": True,
        "createdAt": datetime.now().isoformat(),
    }
    data["reminders"].append(entry)
    save_data(data)
    return entry


def add_routine(payload: dict) -> dict:
    data = load_data()
    entry = {
        "id": new_id(),
        "time": payload["time"],
        "message": payload["message"],
        "days": payload.get("days", list(range(7))),
        "enabled": True,
        "createdAt": datetime.now().isoformat(),
    }
    data["routines"].append(entry)
    save_data(data)
    return entry


def list_reminders() -> list[dict]:
    data = load_data()
    return [item for item in data.get("reminders", []) if item.get("enabled", True)]


def list_routines() -> list[dict]:
    data = load_data()
    return [item for item in data.get("routines", []) if item.get("enabled", True)]


def delete_reminder(item_id: str) -> bool:
    data = load_data()
    before = len(data["reminders"])
    data["reminders"] = [item for item in data["reminders"] if item.get("id") != item_id]
    save_data(data)
    return len(data["reminders"]) < before


def delete_routine(item_id: str) -> bool:
    data = load_data()
    before = len(data["routines"])
    data["routines"] = [item for item in data["routines"] if item.get("id") != item_id]
    save_data(data)
    return len(data["routines"]) < before


def handle_voice(transcript: str) -> dict:
    parsed = parse_command(transcript)

    if not parsed:
        return {"handled": False}

    action = parsed.get("action")

    if action == "add_reminder":
        entry = add_reminder(parsed)
        return {"handled": True, "speechKey": "reminderSet", "entry": entry}

    if action == "add_routine":
        entry = add_routine(parsed)
        return {"handled": True, "speechKey": "routineSet", "entry": entry}

    if action == "list_reminders":
        items = list_reminders()
        return {
            "handled": True,
            "speechKey": "reminderListReady" if items else "reminderListEmpty",
            "items": items,
        }

    if action == "list_routines":
        items = list_routines()
        return {
            "handled": True,
            "speechKey": "routineListReady" if items else "routineListEmpty",
            "items": items,
        }

    if action == "list_calendar":
        cache = sync_calendar(force=True)
        events = cache.get("events", [])
        return {
            "handled": True,
            "speechKey": "calendarListReady" if events else "calendarListEmpty",
            "items": events[:10],
            "calendarError": cache.get("error"),
        }

    if action == "error":
        return {"handled": True, "speechKey": "scheduleError", "reason": parsed.get("reason")}

    return {"handled": False}


def update_calendar_config(payload: dict) -> dict:
    config = load_config()
    calendar = config.setdefault("calendar", {})
    calendar["enabled"] = bool(payload.get("enabled", calendar.get("enabled")))
    if "icsUrl" in payload:
        calendar["icsUrl"] = str(payload.get("icsUrl", "")).strip()
    if "syncMinutes" in payload:
        calendar["syncMinutes"] = int(payload.get("syncMinutes", 15))
    if "lookaheadDays" in payload:
        calendar["lookaheadDays"] = int(payload.get("lookaheadDays", 14))
    save_config(config)
    sync_calendar(force=True)
    return config
