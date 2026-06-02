"""Resolve which speaker profile a schedule belongs to."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SPEAKER_BRIDGE = "http://127.0.0.1:8765"
SPEAKER_ID_DIR = Path(__file__).resolve().parents[1] / "speaker-id"


def _identify_from_mic(seconds: int = 2) -> dict:
    sys.path.insert(0, str(SPEAKER_ID_DIR))
    try:
        from identify import identify_now

        return identify_now(seconds=seconds)
    finally:
        if str(SPEAKER_ID_DIR) in sys.path:
            sys.path.remove(str(SPEAKER_ID_DIR))


def _fetch_active_speaker() -> dict | None:
    try:
        request = urllib.request.Request(f"{SPEAKER_BRIDGE}/v1/active-speaker")
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    if isinstance(payload, dict) and payload.get("profileId"):
        return payload

    return None


def resolve_profile(payload: dict | None = None, *, identify: bool = True) -> tuple[str, str]:
    """Return (profileId, displayName). Prefers live voice ID when identify=True."""
    payload = payload or {}

    if identify:
        try:
            result = _identify_from_mic(seconds=int(payload.get("identifySeconds", 2)))
            profile_id = str(result.get("profileId", "guest"))
            display_name = str(result.get("displayName", "friend"))
            return profile_id, display_name
        except Exception:
            cached = _fetch_active_speaker()
            if cached:
                return str(cached.get("profileId", "guest")), str(
                    cached.get("displayName", "friend")
                )

    profile_id = str(payload.get("profileId", "")).strip()
    display_name = str(payload.get("displayName", "")).strip()

    if profile_id:
        return profile_id, display_name or profile_id

    cached = _fetch_active_speaker()
    if cached:
        return str(cached.get("profileId", "guest")), str(cached.get("displayName", "friend"))

    return "guest", "friend"
