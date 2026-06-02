#!/usr/bin/env python3
"""Offline tests for Pi scheduling (no microphone or network required)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEDULING_DIR = REPO_ROOT / "pi" / "scheduling"
sys.path.insert(0, str(SCHEDULING_DIR))

import parse_voice  # noqa: E402
import storage  # noqa: E402
import commands  # noqa: E402
import scheduler_engine  # noqa: E402
import pi_speak  # noqa: E402


class SchedulingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["SNOOPY_SCHEDULING_DIR"] = self.temp_dir.name
        storage.DATA_DIR = Path(self.temp_dir.name)
        storage.DATA_FILE = storage.DATA_DIR / "scheduling.json"
        storage.CONFIG_FILE = storage.DATA_DIR / "config.json"
        storage.CALENDAR_CACHE_FILE = storage.DATA_DIR / "calendar_caches.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_remind_command(self) -> None:
        parsed = parse_voice.parse_command("hey snoopy remind me at 5 30 to feed the dog")
        self.assertEqual(parsed["action"], "add_reminder")
        self.assertEqual(parsed["time"], "17:30")
        self.assertIn("feed", parsed["message"])

    def test_parse_list_reminders(self) -> None:
        parsed = parse_voice.parse_command("list my reminders")
        self.assertEqual(parsed["action"], "list_reminders")

    def test_add_reminder_scoped_to_profile(self) -> None:
        entry = commands.add_reminder(
            {
                "profileId": "toby",
                "displayName": "Toby",
                "time": "9:00",
                "message": "school",
                "identify": False,
            }
        )
        self.assertEqual(entry["profileId"], "toby")
        items = commands.list_reminders("toby")
        self.assertEqual(len(items), 1)
        self.assertEqual(commands.list_reminders("mum"), [])

    def test_migration_from_legacy_flat_file(self) -> None:
        legacy = {
            "reminders": [{"id": "r1", "time": "10:00", "message": "legacy", "enabled": True}],
            "routines": [],
            "fired": [],
        }
        storage.DATA_FILE.write_text(json.dumps(legacy), encoding="utf-8")
        data = storage.load_data()
        self.assertIn("toby", data["profiles"])
        self.assertEqual(data["profiles"]["toby"]["reminders"][0]["message"], "legacy")

    def test_tick_speaks_and_marks_fired(self) -> None:
        commands.add_reminder(
            {
                "profileId": "toby",
                "displayName": "Toby",
                "time": datetime.now().strftime("%H:%M"),
                "message": "now test",
                "identify": False,
            }
        )

        with patch.object(scheduler_engine, "speak_line") as speak_mock:
            scheduler_engine.tick()
            self.assertTrue(speak_mock.called)

        data = storage.load_data()
        self.assertTrue(data["fired"])

    def test_one_shot_reminder_disables_after_fire(self) -> None:
        commands.add_reminder(
            {
                "profileId": "toby",
                "displayName": "Toby",
                "time": datetime.now().strftime("%H:%M"),
                "message": "once",
                "identify": False,
            }
        )

        with patch.object(scheduler_engine, "speak_line"):
            scheduler_engine.tick()

        data = storage.load_data()
        reminder = data["profiles"]["toby"]["reminders"][0]
        self.assertFalse(reminder.get("enabled", True))

    def test_pi_speak_sanitizes_message(self) -> None:
        line = pi_speak.build_line("Toby", "reminder", "feed the dog!!! @#$")
        self.assertIn("Toby", line)
        self.assertNotIn("@", line)
        self.assertNotIn("#", line)

    def test_per_profile_calendar_config(self) -> None:
        commands.update_calendar_config(
            {
                "profileId": "mum",
                "displayName": "Mum",
                "icsUrl": "https://example.com/mum.ics",
                "enabled": True,
                "identify": False,
            }
        )
        config = storage.load_config()
        self.assertEqual(
            config["profiles"]["mum"]["calendar"]["icsUrl"], "https://example.com/mum.ics"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
