#!/usr/bin/env python3
"""Identify a speaker from a short microphone recording."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from embedding import cosine_similarity, embed_audio, load_embedding, load_meta, load_wav_mono

PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
DEFAULT_THRESHOLD = 0.72
GUEST_PROFILE = {
    "profileId": "guest",
    "displayName": "friend",
    "confidence": 0.0,
}


def record_clip(seconds: int, destination: Path) -> None:
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
        str(seconds),
        str(destination),
    ]
    subprocess.run(command, check=True)


def list_profiles() -> list[Path]:
    if not PROFILES_DIR.exists():
        return []

    return sorted(path for path in PROFILES_DIR.iterdir() if path.is_dir())


def identify_wav(path: Path, threshold: float = DEFAULT_THRESHOLD) -> dict:
    samples = load_wav_mono(path)
    probe = embed_audio(samples)
    best_match = None
    best_score = -1.0

    for profile_dir in list_profiles():
        embedding_path = profile_dir / "embedding.npy"
        meta_path = profile_dir / "meta.json"

        if not embedding_path.exists() or not meta_path.exists():
            continue

        score = cosine_similarity(probe, load_embedding(embedding_path))

        if score > best_score:
            best_score = score
            meta = load_meta(meta_path)
            best_match = {
                "profileId": meta["profileId"],
                "displayName": meta["displayName"],
                "confidence": round(score, 3),
            }

    if best_match and best_score >= threshold:
        return best_match

    guest = dict(GUEST_PROFILE)
    guest["confidence"] = round(max(best_score, 0.0), 3)
    return guest


def identify_now(seconds: int, threshold: float) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        record_clip(seconds, temp_path)
        return identify_wav(temp_path, threshold=threshold)
    finally:
        temp_path.unlink(missing_ok=True)


def build_catalog() -> dict:
    profiles = {
        "toby": {"displayName": "Toby"},
        "guest": {"displayName": "friend"},
    }

    for profile_dir in list_profiles():
        meta_path = profile_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = load_meta(meta_path)
        profiles[meta["profileId"]] = {"displayName": meta["displayName"]}

    return {
        "defaultProfileId": "toby",
        "guestProfileId": "guest",
        "profiles": profiles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Identify a Snoopy speaker.")
    parser.add_argument("--seconds", type=int, default=2, help="Recording length")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--wav", type=Path, help="Identify from an existing wav file")
    parser.add_argument("--catalog", action="store_true", help="Print speaker catalog JSON")
    args = parser.parse_args()

    if args.catalog:
        print(json.dumps(build_catalog(), indent=2))
        return 0

    try:
        if args.wav:
            result = identify_wav(args.wav, threshold=args.threshold)
        else:
            result = identify_now(args.seconds, args.threshold)
    except subprocess.CalledProcessError:
        print(json.dumps(GUEST_PROFILE))
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
