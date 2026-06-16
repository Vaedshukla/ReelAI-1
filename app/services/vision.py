"""Visual analysis — thin wrapper that runs OCR on extracted frames."""

from __future__ import annotations

import logging

import os

logger = logging.getLogger(__name__)

from app.services.ocr import read_frames


def analyze_frames(frames_dir: str) -> str:
    """
    Run OCR on all frames in frames_dir and return combined visual text.

    Args:
        frames_dir: Path to directory containing .jpg frame files.

    Returns:
        Space-separated string of all detected text above confidence threshold.
    """
    logger.info("[Vision] Running visual analysis (OCR)…")

    if not frames_dir or not os.path.exists(frames_dir):
        logger.info(f"[Vision] Frames directory not found: {frames_dir!r}")
        return ""

    visual_text = read_frames(frames_dir)
    logger.info(f"[Vision] Visual text ({len(visual_text)} chars): {visual_text[:120]}…")
    return visual_text
