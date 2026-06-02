#!/usr/bin/env python3
"""Pi scheduling API: per-profile reminders, routines, and calendars."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from calendar_sync import sync_all_calendars, sync_calendar
from commands import (
    add_reminder,
    add_routine,
    delete_reminder,
    delete_routine,
    get_schedule_snapshot,
    handle_voice,
    list_reminders,
    list_routines,
    update_calendar_config,
)
from scheduler_engine import run_scheduler_loop
from storage import ensure_profile, list_profile_ids, load_config


def sync_enrolled_speakers() -> None:
    """Create schedule buckets for every enrolled voice profile."""
    try:
        import sys
        from pathlib import Path

        speaker_dir = Path(__file__).resolve().parents[1] / "speaker-id"
        sys.path.insert(0, str(speaker_dir))
        from identify import build_catalog

        catalog = build_catalog()
        for profile_id, meta in catalog.get("profiles", {}).items():
            ensure_profile(profile_id, meta.get("displayName"))
    except Exception:
        pass

HOST = "127.0.0.1"
PORT = 8766

_stop_event = threading.Event()


def _query_profile(path: str) -> str | None:
    query = parse_qs(urlparse(path).query)
    values = query.get("profileId") or query.get("profile")
    if values:
        return values[0]
    return None


class SchedulingBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}

        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

        return payload if isinstance(payload, dict) else {}

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        profile_id = _query_profile(self.path)

        if path == "/v1/status":
            config = load_config()
            self._send_json(
                200,
                {
                    "ok": True,
                    "profileIds": list_profile_ids(),
                    "defaultProfileId": config.get("defaultProfileId", "toby"),
                    "reminderCount": len(list_reminders(profile_id)),
                    "routineCount": len(list_routines(profile_id)),
                    "speaksOnPi": True,
                },
            )
            return

        if path == "/v1/reminders":
            self._send_json(200, {"reminders": list_reminders(profile_id)})
            return

        if path == "/v1/routines":
            self._send_json(200, {"routines": list_routines(profile_id)})
            return

        if path == "/v1/calendar":
            if not profile_id:
                self._send_json(400, {"error": "profile_required"})
                return
            cache = sync_calendar(profile_id)
            self._send_json(200, {"calendar": cache, "profileId": profile_id})
            return

        if path == "/v1/schedule":
            self._send_json(200, get_schedule_snapshot(profile_id))
            return

        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_body()

        if path == "/v1/voice-command":
            result = handle_voice(str(payload.get("transcript", "")), payload)
            self._send_json(200, result)
            return

        if path == "/v1/reminders":
            required = ("time", "message")
            if not all(payload.get(key) for key in required):
                self._send_json(400, {"error": "missing_fields"})
                return
            entry = add_reminder(payload)
            self._send_json(201, {"reminder": entry})
            return

        if path == "/v1/routines":
            required = ("time", "message")
            if not all(payload.get(key) for key in required):
                self._send_json(400, {"error": "missing_fields"})
                return
            entry = add_routine(payload)
            self._send_json(201, {"routine": entry})
            return

        if path == "/v1/calendar/config":
            if not payload.get("profileId") and not payload.get("identify", True):
                self._send_json(400, {"error": "profile_required"})
                return
            result = update_calendar_config(payload)
            self._send_json(200, result)
            return

        if path == "/v1/calendar/sync":
            if payload.get("profileId"):
                cache = sync_calendar(str(payload["profileId"]), force=True)
                self._send_json(200, {"calendar": cache})
                return
            sync_all_calendars(force=True)
            self._send_json(200, {"ok": True})
            return

        self._send_json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        profile_id = _query_profile(self.path)

        if path.startswith("/v1/reminders/"):
            item_id = path.rsplit("/", 1)[-1]
            self._send_json(200, {"deleted": delete_reminder(item_id, profile_id)})
            return

        if path.startswith("/v1/routines/"):
            item_id = path.rsplit("/", 1)[-1]
            self._send_json(200, {"deleted": delete_routine(item_id, profile_id)})
            return

        self._send_json(404, {"error": "not_found"})


def main() -> None:
    sync_enrolled_speakers()
    worker = threading.Thread(
        target=run_scheduler_loop,
        args=(_stop_event,),
        daemon=True,
    )
    worker.start()

    server = ThreadingHTTPServer((HOST, PORT), SchedulingBridgeHandler)
    print(f"Snoopy scheduling bridge listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    finally:
        _stop_event.set()


if __name__ == "__main__":
    main()
