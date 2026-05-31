#!/usr/bin/env python3
"""Dependency-light checks for Snoopy Pi helper functions."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "snoopy_pi.py"


def load_module():
    spec = importlib.util.spec_from_file_location("snoopy_pi", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    snoopy = load_module()

    assert (
        snoopy.extract_query_after_wake_phrase(
            "hey snoopy what causes rainbows",
            ("hey snoopy",),
        )
        == "what causes rainbows"
    )
    assert snoopy.is_wake_phrase_only("hey snoopy", ("hey snoopy",))
    assert snoopy.extract_query_after_wake_phrase("hello there", ("hey snoopy",)) == ""

    sanitized = snoopy.sanitize_speech("This damn result should be softened.")
    assert "damn" not in sanitized.lower()
    assert "gentle word" in sanitized

    cleaned = snoopy.clean_summary_text(
        """
        AI Overview
        Rainbows form when light bends inside water droplets.
        Show more
        Sources
        """
    )
    assert cleaned == "Rainbows form when light bends inside water droplets."

    print("Snoopy Pi helper checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
