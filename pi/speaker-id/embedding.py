#!/usr/bin/env python3
"""Lightweight voice embeddings for local speaker ID on Raspberry Pi (no cloud)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample

SAMPLE_RATE = 16_000
FRAME_LENGTH = 400
HOP_LENGTH = 160
FEATURE_SIZE = 64


def load_wav_mono(path: Path) -> np.ndarray:
    rate, data = wavfile.read(path)

    if data.ndim > 1:
        data = data.mean(axis=1)

    if data.dtype != np.float32:
        max_value = np.max(np.abs(data)) or 1
        data = data.astype(np.float32) / max_value

    if rate != SAMPLE_RATE:
        target_length = int(len(data) * SAMPLE_RATE / rate)
        data = resample(data, target_length).astype(np.float32)

    peak = np.max(np.abs(data)) or 1.0
    return data / peak


def embed_audio(samples: np.ndarray) -> np.ndarray:
    if samples.size < FRAME_LENGTH:
        samples = np.pad(samples, (0, FRAME_LENGTH - samples.size))

    frames = []
    for start in range(0, len(samples) - FRAME_LENGTH, HOP_LENGTH):
        frame = samples[start : start + FRAME_LENGTH]
        spectrum = np.abs(np.fft.rfft(frame))
        frames.append(spectrum[:FEATURE_SIZE])

    if not frames:
        frames.append(np.abs(np.fft.rfft(samples))[:FEATURE_SIZE])

    embedding = np.mean(frames, axis=0)
    norm = np.linalg.norm(embedding) or 1.0
    return (embedding / norm).astype(np.float32)


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right))


def save_embedding(path: Path, embedding: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, embedding)


def load_embedding(path: Path) -> np.ndarray:
    return np.load(path)


def save_meta(path: Path, profile_id: str, display_name: str) -> None:
    path.write_text(
        json.dumps(
            {
                "profileId": profile_id,
                "displayName": display_name,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_meta(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
