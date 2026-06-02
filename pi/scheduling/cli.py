#!/usr/bin/env python3
"""Manage Snoopy schedules on the Pi without a browser."""

from __future__ import annotations

import argparse
import json
import sys

from commands import (
    add_reminder,
    add_routine,
    get_schedule_snapshot,
    handle_voice,
    update_calendar_config,
)
from profiles import resolve_profile
from storage import ensure_profile, list_profile_ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Snoopy Pi scheduling")
    sub = parser.add_subparsers(dest="command", required=True)

    voice = sub.add_parser("voice", help="Parse a spoken command (identifies speaker first)")
    voice.add_argument("transcript", help='e.g. "hey snoopy remind me at 5 30 to feed the dog"')

    remind = sub.add_parser("remind", help="Add a reminder for a profile")
    remind.add_argument("--at", required=True, help="Time like 17:30 or 5:30pm")
    remind.add_argument("--message", required=True)
    remind.add_argument("--profile", help="Profile id (default: identify from mic)")
    remind.add_argument("--repeat", choices=["daily", "weekdays"])

    routine = sub.add_parser("routine", help="Add a routine step for a profile")
    routine.add_argument("--at", required=True)
    routine.add_argument("--message", required=True)
    routine.add_argument("--profile")
    routine.add_argument("--weekdays", action="store_true")

    cal = sub.add_parser("calendar", help="Set calendar ICS URL for a profile")
    cal.add_argument("--ics-url", required=True)
    cal.add_argument("--profile", required=True)
    cal.add_argument("--disable", action="store_true")

    show = sub.add_parser("show", help="Show schedules")
    show.add_argument("--profile")

    list_profiles = sub.add_parser("profiles", help="List profile ids")

    args = parser.parse_args()

    if args.command == "profiles":
        print("\n".join(list_profile_ids()))
        return 0

    if args.command == "voice":
        result = handle_voice(args.transcript, {"identify": True})
        print(json.dumps(result, indent=2))
        return 0 if result.get("handled") else 1

    if args.command == "remind":
        payload = {
            "time": args.at.replace(".", ""),
            "message": args.message,
            "repeat": args.repeat,
            "identify": not args.profile,
        }
        if args.profile:
            payload["profileId"] = args.profile
            ensure_profile(args.profile)
        entry = add_reminder(payload)
        print(json.dumps(entry, indent=2))
        return 0

    if args.command == "routine":
        payload = {
            "time": args.at.replace(".", ""),
            "message": args.message,
            "days": [0, 1, 2, 3, 4] if args.weekdays else list(range(7)),
            "identify": not args.profile,
        }
        if args.profile:
            payload["profileId"] = args.profile
            ensure_profile(args.profile)
        entry = add_routine(payload)
        print(json.dumps(entry, indent=2))
        return 0

    if args.command == "calendar":
        ensure_profile(args.profile)
        result = update_calendar_config(
            {
                "profileId": args.profile,
                "icsUrl": args.ics_url,
                "enabled": not args.disable,
                "identify": False,
            }
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "show":
        if args.profile:
            print(json.dumps(get_schedule_snapshot(args.profile), indent=2))
        else:
            print(json.dumps(get_schedule_snapshot(), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
