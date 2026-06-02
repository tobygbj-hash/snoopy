"""Parse spoken scheduling commands on the Pi."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

DAY_NAMES = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

WEEKDAYS = [0, 1, 2, 3, 4]
ALL_DAYS = list(range(7))


def normalize_transcript(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[.,!?;:]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def strip_wake_prefix(text: str) -> str:
    prefixes = (
        "hey snoopy",
        "hi snoopy",
        "okay snoopy",
        "ok snoopy",
        "hello snoopy",
        "yo snoopy",
        "wake up snoopy",
        "attention snoopy",
    )

    working = normalize_transcript(text)

    for prefix in prefixes:
        if working == prefix:
            return ""
        if working.startswith(prefix + " "):
            working = working[len(prefix) + 1 :].strip()

    return working


def parse_time_token(token: str) -> str | None:
    token = token.strip().lower().replace(".", "")

    match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", token)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    if not meridiem and hour <= 12 and "am" not in token and "pm" not in token:
        # Spoken without am/pm: treat 1-7 as PM-ish for routines, else 24h style
        if 1 <= hour <= 7:
            hour += 12

    if hour > 23 or minute > 59:
        return None

    return f"{hour:02d}:{minute:02d}"


def extract_time_and_rest(text: str) -> tuple[str | None, str]:
    patterns = [
        r"\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        time_value = parse_time_token(match.group(1))
        if not time_value:
            continue

        before = text[: match.start()].strip()
        after = text[match.end() :].strip()
        rest = f"{before} {after}".strip()
        rest = re.sub(r"\s+", " ", rest)
        return time_value, rest

    return None, text


def clean_message(text: str) -> str:
    message = text
    for prefix in (
        r"^to\s+",
        r"^for\s+",
        r"^that\s+",
        r"^about\s+",
        r"^remind me\s+",
        r"^add\s+",
        r"^put\s+",
    ):
        message = re.sub(prefix, "", message).strip()

    message = re.sub(r"\s+", " ", message)
    return message[:120]


def parse_days(text: str) -> list[int]:
    if "weekday" in text or "school day" in text:
        return WEEKDAYS
    if "every day" in text or "daily" in text or "each day" in text:
        return ALL_DAYS

    found: list[int] = []

    for name, index in DAY_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            if index not in found:
                found.append(index)

    return sorted(found) if found else ALL_DAYS


def parse_command(transcript: str) -> dict | None:
    text = strip_wake_prefix(transcript)

    if not text:
        return None

    if re.search(r"\b(list|show|what are)\b.*\b(reminders?)\b", text):
        return {"action": "list_reminders"}

    if re.search(r"\b(list|show|what is on)\b.*\b(routines?)\b", text):
        return {"action": "list_routines"}

    if re.search(r"\b(list|show)\b.*\b(calendar|schedule)\b", text):
        return {"action": "list_calendar"}

    if re.search(r"\bremind me\b", text) or re.search(r"\bset a reminder\b", text):
        time_value, rest = extract_time_and_rest(text)
        if not time_value:
            return {"action": "error", "reason": "no_time"}

        message = clean_message(rest)
        if not message:
            return {"action": "error", "reason": "no_message"}

        repeat = None
        if "every day" in text or "daily" in text:
            repeat = "daily"
        elif "weekday" in text:
            repeat = "weekdays"

        target_date = date.today().isoformat()
        return {
            "action": "add_reminder",
            "time": time_value,
            "date": target_date,
            "message": message,
            "repeat": repeat,
        }

    if re.search(r"\b(routine|every day at|routine at)\b", text) or re.search(
        r"\badd\b.*\bto my routine\b", text
    ):
        time_value, rest = extract_time_and_rest(text)
        if not time_value:
            return {"action": "error", "reason": "no_time"}

        message = clean_message(rest)
        if not message:
            return {"action": "error", "reason": "no_message"}

        days = parse_days(text)
        return {
            "action": "add_routine",
            "time": time_value,
            "message": message,
            "days": days,
        }

    return None


def next_fire_date_for_time(time_hhmm: str, repeat: str | None) -> date:
    hour, minute = (int(part) for part in time_hhmm.split(":"))
    now = datetime.now()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if candidate <= now:
        candidate += timedelta(days=1)

    if repeat == "weekdays":
        while candidate.weekday() > 4:
            candidate += timedelta(days=1)

    return candidate.date()
