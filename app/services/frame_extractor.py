"""Frame extraction from video using OpenCV."""

from __future__ import annotations

import logging
import os

import cv2  # type: ignore[import]

logger = logging.getLogger(__name__)


def extract_frames(video_path: str, output_dir: str, interval_sec: int = 2) -> int:
    """
    Extract one frame every `interval_sec` seconds from a video file.

    Args:
        video_path:   Path to the input video file.
        output_dir:   Directory to save extracted .jpg frames.
        interval_sec: Interval between captured frames (seconds).

    Returns:
        Number of frames saved.

    Raises:
        RuntimeError: If the video file cannot be opened.
    """
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    fps: float = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        logger.warning(f"[FrameExtractor] Warning: FPS={fps} — defaulting to 1 frame/sec.")
        fps = 1.0

    frame_interval = max(1, int(fps * interval_sec))
    count = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved += 1

        count += 1

    cap.release()
    logger.info(f"[FrameExtractor] Saved {saved} frames from {count} total frames (fps={fps:.1f}).")
    return saved