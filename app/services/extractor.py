"""Lazy-loaded Whisper model singleton with configurable size and device."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import torch

from app.config import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    BASE_DIR,
    CLEANUP_AFTER_PROCESSING,
    DEVICE_PREFERENCE,
    FRAME_INTERVAL_SEC,
    WHISPER_MODEL_SIZE,
)
from app.services.frame_extractor import extract_frames

logger = logging.getLogger(__name__)

# ── Model singleton (lazy-loaded on first request) ────────────────────────────
_whisper_model = None


def _get_device() -> str:
    if DEVICE_PREFERENCE == "cuda":
        return "cuda"
    if DEVICE_PREFERENCE == "cpu":
        return "cpu"
    # auto
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper  # type: ignore[import]

        device = _get_device()
        logger.info(f"[Extractor] Loading Whisper '{WHISPER_MODEL_SIZE}' on {device}…")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE).to(device)
        logger.info("[Extractor] Whisper ready.")
    return _whisper_model


def _check_binary(name: str) -> None:
    """Raise a clear RuntimeError if a required binary is missing."""
    if shutil.which(name) is None:
        raise RuntimeError(
            f"Required binary '{name}' not found in PATH. "
            f"Please install it and make sure it is accessible from the command line."
        )


def extract(url: str) -> dict:
    """
    Full extraction pipeline for a social-media reel URL.

    Returns:
        {
            "transcript": str,
            "video_path": str,
            "frames_dir": str,
        }

    Raises:
        RuntimeError  – missing binaries or download/extraction failures
        ValueError    – bad / unsupported URL
    """

    # ── Validate URL ──────────────────────────────────────────────────────────
    url = url.strip()
    if not url:
        raise ValueError("URL must not be empty.")

    # Strip query params (avoids yt-dlp auth issues on some platforms)
    clean_url = url.split("?")[0]

    # ── Check binaries ────────────────────────────────────────────────────────
    _check_binary("yt-dlp")
    _check_binary("ffmpeg")

    # ── Setup temp paths ──────────────────────────────────────────────────────
    os.makedirs(BASE_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    video_path = os.path.join(BASE_DIR, f"{file_id}.mp4")
    audio_path = os.path.join(BASE_DIR, f"{file_id}.wav")
    frames_dir = os.path.join(BASE_DIR, f"{file_id}_frames")

    try:
        # ── 1. Download video ─────────────────────────────────────────────────
        logger.info(f"[Extractor] Downloading: {clean_url}")
        result = subprocess.run(
            ["yt-dlp", "-f", "mp4/bestvideo+bestaudio/best", "-o", video_path, clean_url],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"yt-dlp failed to download the video.\n"
                f"URL: {clean_url}\n"
                f"stderr: {result.stderr.strip()}"
            )

        if not os.path.exists(video_path):
            raise RuntimeError(
                f"yt-dlp exited OK but the video file was not created at '{video_path}'. "
                "The URL may not be a downloadable video (try a direct reel URL)."
            )

        # ── 2. Extract audio ─────────────────────────────────────────────────
        logger.info("[Extractor] Extracting audio…")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-ar", str(AUDIO_SAMPLE_RATE), "-ac", str(AUDIO_CHANNELS), audio_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed to extract audio.\nstderr: {result.stderr.strip()}"
            )

        # ── 3. Extract frames ─────────────────────────────────────────────────
        logger.info("[Extractor] Extracting frames…")
        frame_count = extract_frames(
            video_path=video_path,
            output_dir=frames_dir,
            interval_sec=FRAME_INTERVAL_SEC,
        )
        logger.info(f"[Extractor] {frame_count} frame(s) extracted.")

        # ── 4. Transcribe with Whisper ────────────────────────────────────────
        logger.info("[Extractor] Running Whisper…")
        model = _get_model()
        result_w = model.transcribe(audio_path)
        transcript: str = result_w.get("text", "").strip()
        logger.info(f"[Extractor] Transcript ({len(transcript)} chars): {transcript[:120]}…")

        return {
            "transcript": transcript,
            "video_path": video_path,
            "frames_dir": frames_dir,
        }

    finally:
        # ── Cleanup temp files (configurable) ─────────────────────────────────
        if CLEANUP_AFTER_PROCESSING:
            for path in [video_path, audio_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
            try:
                if os.path.isdir(frames_dir):
                    shutil.rmtree(frames_dir, ignore_errors=True)
            except OSError:
                pass
