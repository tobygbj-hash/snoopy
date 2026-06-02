"""Speak reminders on the Pi speaker (no browser). Uses espeak-ng or espeak."""

from __future__ import annotations

import re
import shutil
import subprocess


def sanitize_words(text: str, limit: int = 120) -> str:
    cleaned = re.sub(r"[^\w\s.,'-]", " ", str(text or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:limit] or "your reminder"


def build_line(display_name: str, kind: str, message: str) -> str:
    name = sanitize_words(display_name, 40)
    detail = sanitize_words(message)

    if kind == "routine":
        return f"Hi {name}, it is time for {detail}."
    if kind == "calendar":
        return f"Hi {name}, your calendar says {detail}."
    return f"Hi {name}, friendly reminder about {detail}."


def speak_line(display_name: str, kind: str, message: str) -> bool:
    line = build_line(display_name, kind, message)
    binary = shutil.which("espeak-ng") or shutil.which("espeak")

    if not binary:
        print(f"[snoopy-scheduler] {line}")
        return False

    try:
        subprocess.run(
            [binary, "-s", "150", "-a", "200", line],
            check=False,
            timeout=30,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        print(f"[snoopy-scheduler] {line}")
        return False
