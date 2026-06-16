"""Lazy-loaded EasyOCR reader singleton with configurable GPU, languages, and threshold."""

from __future__ import annotations

import logging
import os
from typing import Optional

import torch

from app.config import (
    DEVICE_PREFERENCE,
    OCR_CONFIDENCE_THRESHOLD,
    OCR_LANGUAGES,
)

logger = logging.getLogger(__name__)

# ── Reader singleton (lazy-loaded on first request) ────────────────────────────
_reader = None


def _use_gpu() -> bool:
    if DEVICE_PREFERENCE == "cpu":
        return False
    if DEVICE_PREFERENCE == "cuda":
        return True
    # auto
    return torch.cuda.is_available()


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr  # type: ignore[import]

        gpu = _use_gpu()
        logger.info(f"[OCR] Loading EasyOCR (languages={OCR_LANGUAGES}, gpu={gpu})…")
        _reader = easyocr.Reader(OCR_LANGUAGES, gpu=gpu)
        logger.info("[OCR] EasyOCR ready.")
    return _reader


def read_frames(frames_dir: str) -> str:
    """
    Run OCR on every .jpg in frames_dir and return all text above the
    confidence threshold concatenated into a single string.
    """
    if not os.path.exists(frames_dir):
        logger.info(f"[OCR] Frames directory not found: {frames_dir}")
        return ""

    jpg_files = sorted(
        f for f in os.listdir(frames_dir) if f.lower().endswith(".jpg")
    )

    if not jpg_files:
        logger.info("[OCR] No .jpg frames found.")
        return ""

    reader = _get_reader()
    texts: list[str] = []

    for filename in jpg_files:
        path = os.path.join(frames_dir, filename)
        try:
            results = reader.readtext(path)
            for (_, text, confidence) in results:
                if confidence >= OCR_CONFIDENCE_THRESHOLD:
                    texts.append(text.strip())
        except Exception as e:
            logger.info(f"[OCR] Failed to read {filename}: {e}")
            continue

    combined = " ".join(t for t in texts if t)
    logger.info(f"[OCR] Extracted {len(texts)} text segment(s) → {len(combined)} chars.")
    return combined