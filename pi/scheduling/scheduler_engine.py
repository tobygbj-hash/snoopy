"""Check schedules for every profile and speak on the Pi (no browser)."""

from __future__ import annotations

import threading
from datetime import date, datetime

from calendar_sync import events_due_now, sync_all_calendars
from pi_speak import speak_line
from copy import deepcopy

from storage import (
    DEFAULT_PROFILE_BUCKET,
    get_display_name,
    list_profile_ids,
    load_data,
    prune_fired,
    save_data,
    get_calendar_cache,
)


def _already_fired(
    data: dict, kind: str, item_id: str, on_date: str, profile_id: str
) -> bool:
    for entry in data.get("fired", []):
        if (
            entry.get("kind") == kind
            and entry.get("id") == item_id
            and entry.get("date") == on_date
            and entry.get("profileId") == profile_id
        ):
            return True
    return False


def _mark_fired(
    data: dict, kind: str, item_id: str, on_date: str, profile_id: str
) -> None:
    data["fired"].append(
        {"kind": kind, "id": item_id, "date": on_date, "profileId": profile_id}
    )
    prune_fired(data)


def _time_matches(now: datetime, hhmm: str) -> bool:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return now.hour == hour and now.minute == minute


def _routine_runs_today(routine: dict, today: date) -> bool:
    days = routine.get("days", [])
    if not days:
        return True
    return today.weekday() in days


def tick_profile(profile_id: str, data: dict, today: str, now: datetime) -> None:
    display_name = get_display_name(profile_id)
    profiles = data.setdefault("profiles", {})
    bucket = profiles.setdefault(profile_id, deepcopy(DEFAULT_PROFILE_BUCKET))

    for reminder in bucket.get("reminders", []):
        item_id = reminder.get("id")
        if not reminder.get("enabled", True) or not item_id or not reminder.get("time"):
            continue

        if not _time_matches(now, reminder["time"]):
            continue

        if _already_fired(data, "reminder", item_id, today, profile_id):
            continue

        message = reminder.get("message", "your reminder")
        speak_line(display_name, "reminder", message)
        _mark_fired(data, "reminder", item_id, today, profile_id)

        if reminder.get("repeat") not in ("daily", "weekdays"):
            reminder["enabled"] = False

    for routine in bucket.get("routines", []):
        item_id = routine.get("id")
        if not routine.get("enabled", True) or not item_id or not routine.get("time"):
            continue

        if not _routine_runs_today(routine, now.date()):
            continue

        if not _time_matches(now, routine["time"]):
            continue

        if _already_fired(data, "routine", item_id, today, profile_id):
            continue

        message = routine.get("message", "your routine step")
        speak_line(display_name, "routine", message)
        _mark_fired(data, "routine", item_id, today, profile_id)

    calendar_cache = get_calendar_cache(profile_id)
    for event in events_due_now(calendar_cache):
        item_id = event.get("id", "calendar")
        if _already_fired(data, "calendar", item_id, today, profile_id):
            continue

        message = event.get("summary", "something on your calendar")
        speak_line(display_name, "calendar", message)
        _mark_fired(data, "calendar", item_id, today, profile_id)


def tick() -> None:
    data = load_data()
    today = date.today().isoformat()
    now = datetime.now()

    for profile_id in list_profile_ids():
        tick_profile(profile_id, data, today, now)

    save_data(data)


def run_scheduler_loop(stop_event: threading.Event, interval_seconds: int = 30) -> None:
    while not stop_event.is_set():
        try:
            sync_all_calendars()
            tick()
        except Exception:
            pass
        stop_event.wait(interval_seconds)
