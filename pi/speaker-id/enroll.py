#!/usr/bin/env python3
"""Enroll a speaker profile on the Pi (local storage only)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from embedding import embed_audio, load_wav_mono, save_embedding, save_meta

PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
SAMPLE_SECONDS = 3
PROMPTS = [
    "Please say: Hi Snoopy, I am ready to search.",
    "Please say: Snoopy, help me find something friendly.",
    "Please say: I am speaking so you know my voice.",
]


def record_sample(destination: Path) -> None:
    command = [
        "arecord",
        "-q",
        "-f",
        "S16_LE",
        "-r",
        "16000",
        "-c",
        "1",
        "-d",
        str(SAMPLE_SECONDS),
        str(destination),
    ]
    subprocess.run(command, check=True)


def enroll(profile_id: str, display_name: str) -> None:
    profile_dir = PROFILES_DIR / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    embeddings = []

    print(f"Enrolling {display_name} as profile '{profile_id}'.\n")

    for index, prompt in enumerate(PROMPTS, start=1):
        print(f"Sample {index}/{len(PROMPTS)}: {prompt}")
        input("Press Enter when you are ready to record… ")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            record_sample(temp_path)
            samples = load_wav_mono(temp_path)
            embeddings.append(embed_audio(samples))
            sample_path = profile_dir / f"sample-{index}.wav"
            sample_path.write_bytes(temp_path.read_bytes())
            print("Recorded.\n")
        finally:
            temp_path.unlink(missing_ok=True)

    mean_embedding = np.mean(np.stack(embeddings, axis=0), axis=0).astype(np.float32)
    save_embedding(profile_dir / "embedding.npy", mean_embedding)
    save_meta(profile_dir / "meta.json", profile_id, display_name)
    print(f"Saved voice profile for {display_name} at {profile_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enroll a Snoopy speaker profile.")
    parser.add_argument("--id", required=True, help="Profile id, e.g. toby or mum")
    parser.add_argument("--name", required=True, help="Display name Snoopy should say")
    args = parser.parse_args()

    profile_id = args.id.strip().lower().replace(" ", "-")
    display_name = args.name.strip()

    if not profile_id or not display_name:
        print("Profile id and display name are required.", file=sys.stderr)
        return 1

    try:
        enroll(profile_id, display_name)
    except subprocess.CalledProcessError:
        print("Recording failed. Install alsa-utils (arecord) and check your microphone.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
