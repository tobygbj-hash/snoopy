#!/usr/bin/env python3
"""Always-on Raspberry Pi voice assistant for Toby.

Snoopy listens for a wake phrase, uses the exact spoken words as a Google query,
extracts Google's AI Overview when it is present, and reads it aloud locally.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - handled at runtime on the Pi.
    BeautifulSoup = None

try:
    import sounddevice as sd
    from vosk import KaldiRecognizer, Model
except ImportError:  # pragma: no cover - handled at runtime on the Pi.
    sd = None
    KaldiRecognizer = None
    Model = None

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - handled at runtime on the Pi.
    PlaywrightTimeoutError = None
    sync_playwright = None


GOOGLE_SEARCH_URL = "https://www.google.com/search"
DEFAULT_WAKE_PHRASES = ("hey snoopy", "ok snoopy", "snoopy")
DEFAULT_MODEL_PATH = Path.home() / "snoopy-model"
DEFAULT_CHROMIUM_PATHS = (
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
)

APPROVED_LINES = {
    "ready": "Hi Toby, Snoopy is ready.",
    "listening": "I am listening, Toby.",
    "searching": "Toby, I am checking Google for that.",
    "reading": "Toby, here is the short summary.",
    "no_summary": "Toby, I could not find a Google AI Overview for that search yet.",
    "error": "Toby, I had trouble getting that summary.",
    "stopped": "All set, Toby. Snoopy is stopping.",
}

BLOCKED_WORD_CODES = (
    (97, 115, 115, 104, 111, 108, 101),
    (98, 97, 115, 116, 97, 114, 100),
    (98, 105, 116, 99, 104),
    (99, 117, 110, 116),
    (100, 97, 109, 110),
    (100, 105, 99, 107),
    (102, 117, 99, 107),
    (104, 101, 108, 108),
    (112, 105, 115, 115),
    (115, 104, 105, 116),
)
BLOCKED_WORDS = tuple("".join(chr(code) for code in codes) for codes in BLOCKED_WORD_CODES)


@dataclass(frozen=True)
class AssistantConfig:
    chromium_path: str | None
    headless: bool
    model_path: Path
    sample_rate: int
    wake_phrases: tuple[str, ...]


class Speaker:
    """Small wrapper around common Raspberry Pi text-to-speech commands."""

    def __init__(self) -> None:
        self._command = shutil.which("spd-say") or shutil.which("espeak")

    def say_key(self, key: str) -> None:
        self.say(APPROVED_LINES[key])

    def say(self, text: str) -> None:
        safe_text = sanitize_speech(text)

        if self._command:
            subprocess.run([self._command, safe_text], check=False)
            return

        print(safe_text, flush=True)


class VoskListener:
    """Offline microphone listener using a local Vosk model."""

    def __init__(self, config: AssistantConfig) -> None:
        if sd is None or KaldiRecognizer is None or Model is None:
            raise RuntimeError(
                "Missing voice dependencies. Install requirements.txt on the Pi first."
            )

        if not config.model_path.exists():
            raise RuntimeError(
                f"Vosk model not found at {config.model_path}. See pi-assistant/README.md."
            )

        self._audio: queue.Queue[bytes] = queue.Queue()
        self._config = config
        self._model = Model(str(config.model_path))
        self._recognizer = KaldiRecognizer(self._model, config.sample_rate)
        self._stream = sd.RawInputStream(
            samplerate=config.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._on_audio,
        )

    def _on_audio(self, indata: bytes, frames: int, time_info: object, status: object) -> None:
        del frames, time_info

        if status:
            print(status, file=sys.stderr)

        self._audio.put(bytes(indata))

    def listen_forever(self) -> Iterable[str]:
        with self._stream:
            while True:
                data = self._audio.get()

                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = normalize_space(result.get("text", ""))

                    if text:
                        yield text


class GoogleAiOverviewReader:
    """Best-effort Google AI Overview reader using a background Chromium page."""

    def __init__(self, config: AssistantConfig) -> None:
        if sync_playwright is None:
            raise RuntimeError(
                "Missing browser dependency. Install requirements.txt and run playwright install."
            )

        self._config = config
        self._playwright = None
        self._browser = None
        self._profile_dir = tempfile.TemporaryDirectory(prefix="snoopy-pi-chromium-")

    def __enter__(self) -> "GoogleAiOverviewReader":
        self._playwright = sync_playwright().start()
        launch_options = {
            "headless": self._config.headless,
            "args": [
                "--disable-background-networking",
                "--disable-sync",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        }

        if self._config.chromium_path:
            launch_options["executable_path"] = self._config.chromium_path

        self._browser = self._playwright.chromium.launch_persistent_context(
            self._profile_dir.name,
            **launch_options,
        )
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback

        if self._browser:
            self._browser.close()

        if self._playwright:
            self._playwright.stop()

        self._profile_dir.cleanup()

    def read_overview(self, query: str) -> str:
        if not self._browser:
            raise RuntimeError("Browser is not running.")

        page = self._browser.new_page()

        try:
            page.goto(build_google_url(query), wait_until="domcontentloaded", timeout=25000)
            wait_for_possible_overview(page)
            html = page.content()
            return extract_ai_overview(html)
        finally:
            page.close()


class SnoopyPiAssistant:
    def __init__(self, config: AssistantConfig) -> None:
        self._config = config
        self._speaker = Speaker()
        self._stopping = False

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)
        self._speaker.say_key("ready")

        listener = VoskListener(self._config)

        awaiting_query = False

        with GoogleAiOverviewReader(self._config) as reader:
            for phrase in listener.listen_forever():
                if self._stopping:
                    break

                if awaiting_query:
                    query = phrase
                    awaiting_query = False
                elif is_wake_phrase_only(phrase, self._config.wake_phrases):
                    self._speaker.say_key("listening")
                    awaiting_query = True
                    continue
                else:
                    query = extract_query_after_wake_phrase(phrase, self._config.wake_phrases)

                if not query:
                    continue

                self._speaker.say_key("searching")

                try:
                    overview = reader.read_overview(query)
                except Exception as error:  # pragma: no cover - runtime diagnostics.
                    print(f"Failed to read overview: {error}", file=sys.stderr)
                    self._speaker.say_key("error")
                    continue

                if overview:
                    self._speaker.say(f"{APPROVED_LINES['reading']} {overview}")
                else:
                    self._speaker.say_key("no_summary")

        self._speaker.say_key("stopped")

    def _stop(self, signum: int, frame: object) -> None:
        del signum, frame
        self._stopping = True


def build_google_url(query: str) -> str:
    return f"{GOOGLE_SEARCH_URL}?{urlencode({'q': query})}"


def wait_for_possible_overview(page: object) -> None:
    for selector in (
        "text=/AI Overview/i",
        "text=/AI Mode/i",
        "[data-attrid*='AI']",
    ):
        try:
            page.wait_for_selector(selector, timeout=2500)
            return
        except PlaywrightTimeoutError:
            continue

    time.sleep(1.0)


def extract_ai_overview(html: str) -> str:
    if BeautifulSoup is None:
        raise RuntimeError("Missing BeautifulSoup. Install requirements.txt on the Pi first.")

    soup = BeautifulSoup(html, "html.parser")
    marker = find_ai_marker(soup)

    if not marker:
        return ""

    container = find_summary_container(marker)
    text = clean_summary_text(container.get_text("\n") if container else marker.get_text("\n"))
    return shorten_summary(text)


def find_ai_marker(soup: BeautifulSoup) -> object | None:
    for text_node in soup.find_all(string=re.compile(r"\bAI (Overview|Mode)\b", re.I)):
        parent = text_node.parent

        if parent:
            return parent

    return None


def find_summary_container(marker: object) -> object:
    current = marker
    best = marker

    for _ in range(8):
        if not current:
            break

        text = clean_summary_text(current.get_text("\n"))

        if 160 < len(text) < 5000:
            best = current

        current = getattr(current, "parent", None)

    return best


def clean_summary_text(text: str) -> str:
    ignored = re.compile(
        r"^(AI Overview|AI Mode|Show more|Show less|Sources?|Listen|Share|\d+)$",
        re.I,
    )
    lines = [
        normalize_space(line)
        for line in text.splitlines()
        if normalize_space(line) and not ignored.match(normalize_space(line))
    ]
    cleaned = " ".join(line for line in lines if not line.startswith("http"))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^(AI Overview|AI Mode)\s+", "", cleaned, flags=re.I)
    return sanitize_speech(cleaned)


def shorten_summary(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text

    boundary = text[:limit].rfind(".")

    if boundary > 300:
        return text[: boundary + 1]

    return f"{text[: limit - 3].strip()}..."


def sanitize_speech(text: str) -> str:
    safe = text

    for word in BLOCKED_WORDS:
        safe = re.sub(rf"\b{re.escape(word)}\b", "gentle word", safe, flags=re.I)

    return safe


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_wake_phrase_only(phrase: str, wake_phrases: Iterable[str]) -> bool:
    normalized = normalize_space(phrase).lower()
    return any(normalized == wake_phrase.lower() for wake_phrase in wake_phrases)


def extract_query_after_wake_phrase(phrase: str, wake_phrases: Iterable[str]) -> str:
    normalized = normalize_space(phrase).lower()

    for wake_phrase in wake_phrases:
        wake = wake_phrase.lower()

        if normalized.startswith(f"{wake} "):
            return normalize_space(phrase[len(wake_phrase) :])

    return ""


def detect_chromium_path(explicit_path: str | None) -> str | None:
    if explicit_path:
        return explicit_path

    for path in DEFAULT_CHROMIUM_PATHS:
        if Path(path).exists():
            return path

    return None


def parse_args() -> AssistantConfig:
    parser = argparse.ArgumentParser(description="Run Snoopy on a Raspberry Pi.")
    parser.add_argument("--chromium-path", default=os.getenv("SNOOPY_CHROMIUM_PATH"))
    parser.add_argument("--headed", action="store_true", help="Show Chromium while debugging.")
    parser.add_argument("--model-path", default=os.getenv("SNOOPY_VOSK_MODEL", DEFAULT_MODEL_PATH))
    parser.add_argument("--sample-rate", default=16000, type=int)
    parser.add_argument(
        "--wake-phrase",
        action="append",
        dest="wake_phrases",
        help="Wake phrase to listen for. Can be used more than once.",
    )
    args = parser.parse_args()

    return AssistantConfig(
        chromium_path=detect_chromium_path(args.chromium_path),
        headless=not args.headed,
        model_path=Path(args.model_path).expanduser(),
        sample_rate=args.sample_rate,
        wake_phrases=tuple(args.wake_phrases or DEFAULT_WAKE_PHRASES),
    )


def main() -> int:
    config = parse_args()
    assistant = SnoopyPiAssistant(config)
    assistant.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
