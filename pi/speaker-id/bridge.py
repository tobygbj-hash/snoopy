#!/usr/bin/env python3
"""Local-only HTTP bridge between Snoopy in Chromium and speaker-id on the Pi."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from identify import build_catalog, identify_now

HOST = "127.0.0.1"
PORT = 8765

active_speaker: dict = {
    "profileId": "guest",
    "displayName": "friend",
    "confidence": 0.0,
}
state_lock = threading.Lock()


class SpeakerBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/v1/active-speaker":
            with state_lock:
                self._send_json(200, dict(active_speaker))
            return

        if self.path == "/v1/catalog":
            self._send_json(200, build_catalog())
            return

        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/identify-now":
            self._send_json(404, {"error": "not_found"})
            return

        result = identify_now(seconds=2)

        with state_lock:
            active_speaker.clear()
            active_speaker.update(result)

        self._send_json(200, result)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SpeakerBridgeHandler)
    print(f"Snoopy speaker bridge listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
