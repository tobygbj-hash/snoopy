#!/usr/bin/env python3
"""Local scheduling bridge: reminders, routines, and optional calendar ICS sync."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from calendar_sync import load_calendar_cache, sync_calendar
from commands import (
    add_reminder,
    add_routine,
    delete_reminder,
    delete_routine,
    handle_voice,
    list_reminders,
    list_routines,
    update_calendar_config,
)
from scheduler_engine import ack_pending, peek_pending, run_scheduler_loop
from storage import load_config, load_data

HOST = "127.0.0.1"
PORT = 8766

_stop_event = threading.Event()


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
        path = urlparse(self.path).path

        if path == "/v1/status":
            config = load_config()
            self._send_json(
                200,
                {
                    "ok": True,
                    "calendar": config.get("calendar", {}),
                    "reminderCount": len(list_reminders()),
                    "routineCount": len(list_routines()),
                },
            )
            return

        if path == "/v1/reminders":
            self._send_json(200, {"reminders": list_reminders()})
            return

        if path == "/v1/routines":
            self._send_json(200, {"routines": list_routines()})
            return

        if path == "/v1/calendar":
            cache = sync_calendar()
            self._send_json(
                200,
                {
                    "calendar": cache,
                    "config": load_config().get("calendar", {}),
                },
            )
            return

        if path == "/v1/pending-speech":
            self._send_json(200, {"pending": peek_pending()})
            return

        if path == "/v1/schedule":
            self._send_json(
                200,
                {
                    "reminders": list_reminders(),
                    "routines": list_routines(),
                    "calendar": load_calendar_cache(),
                    "config": load_config(),
                },
            )
            return

        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_body()

        if path == "/v1/voice-command":
            result = handle_voice(str(payload.get("transcript", "")))
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
            config = update_calendar_config(payload)
            self._send_json(200, {"config": config})
            return

        if path == "/v1/calendar/sync":
            cache = sync_calendar(force=True)
            self._send_json(200, {"calendar": cache})
            return

        if path == "/v1/pending-speech/ack":
            entry_id = str(payload.get("id", ""))
            ok = ack_pending(entry_id) if entry_id else False
            self._send_json(200, {"ok": ok})
            return

        self._send_json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path

        if path.startswith("/v1/reminders/"):
            item_id = path.rsplit("/", 1)[-1]
            self._send_json(200, {"deleted": delete_reminder(item_id)})
            return

        if path.startswith("/v1/routines/"):
            item_id = path.rsplit("/", 1)[-1]
            self._send_json(200, {"deleted": delete_routine(item_id)})
            return

        self._send_json(404, {"error": "not_found"})


def main() -> None:
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
