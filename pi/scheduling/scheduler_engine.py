"""Find due reminders, routines, and calendar events; queue spoken announcements."""

from __future__ import annotations

import threading
from datetime import date, datetime, timedelta

from calendar_sync import events_due_now, load_calendar_cache, sync_calendar
from storage import load_data, load_config, new_id, prune_fired, save_data

_pending: list[dict] = []
_pending_lock = threading.Lock()

FIRED_KINDS = ("reminder", "routine", "calendar")


def _already_fired(data: dict, kind: str, item_id: str, on_date: str) -> bool:
    for entry in data.get("fired", []):
        if (
            entry.get("kind") == kind
            and entry.get("id") == item_id
            and entry.get("date") == on_date
        ):
            return True
    return False


def _mark_fired(data: dict, kind: str, item_id: str, on_date: str) -> None:
    data["fired"].append({"kind": kind, "id": item_id, "date": on_date})
    prune_fired(data)


def _enqueue(kind: str, item_id: str, message: str, display_name: str) -> None:
    entry = {
        "id": new_id(),
        "kind": kind,
        "itemId": item_id,
        "message": message[:120],
        "displayName": display_name,
        "createdAt": datetime.now().isoformat(),
    }

    with _pending_lock:
        _pending.append(entry)


def pop_pending() -> list[dict]:
    with _pending_lock:
        items = list(_pending)
        _pending.clear()
    return items


def peek_pending() -> list[dict]:
    with _pending_lock:
        return list(_pending)


def ack_pending(entry_id: str) -> bool:
    with _pending_lock:
        before = len(_pending)
        _pending[:] = [item for item in _pending if item.get("id") != entry_id]
        return len(_pending) < before


def _time_matches(now: datetime, hhmm: str) -> bool:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return now.hour == hour and now.minute == minute


def _routine_runs_today(routine: dict, today: date) -> bool:
    days = routine.get("days", [])
    if not days:
        return True
    return today.weekday() in days


def tick() -> None:
    config = load_config()
    display_name = str(config.get("displayName", "Toby"))
    data = load_data()
    today = date.today().isoformat()
    now = datetime.now()

    for reminder in data.get("reminders", []):
        item_id = reminder.get("id")
        if not item_id or not reminder.get("time"):
            continue

        if not _time_matches(now, reminder["time"]):
            continue

        if _already_fired(data, "reminder", item_id, today):
            continue

        message = reminder.get("message", "your reminder")
        _enqueue("reminder", item_id, message, display_name)
        _mark_fired(data, "reminder", item_id, today)

        repeat = reminder.get("repeat")
        if repeat not in ("daily", "weekdays"):
            reminder["enabled"] = False

    for routine in data.get("routines", []):
        item_id = routine.get("id")
        if not item_id or not routine.get("time"):
            continue

        if not _routine_runs_today(routine, now.date()):
            continue

        if not _time_matches(now, routine["time"]):
            continue

        if _already_fired(data, "routine", item_id, today):
            continue

        message = routine.get("message", "your routine step")
        _enqueue("routine", item_id, message, display_name)
        _mark_fired(data, "routine", item_id, today)

    calendar_cache = load_calendar_cache()
    for event in events_due_now(calendar_cache):
        item_id = event.get("id", "calendar")
        if _already_fired(data, "calendar", item_id, today):
            continue

        message = event.get("summary", "something on your calendar")
        _enqueue("calendar", item_id, message, display_name)
        _mark_fired(data, "calendar", item_id, today)

    save_data(data)


def run_scheduler_loop(stop_event: threading.Event, interval_seconds: int = 30) -> None:
    while not stop_event.is_set():
        try:
            sync_calendar()
            tick()
        except Exception:
            pass
        stop_event.wait(interval_seconds)
