"""
Centralized configuration for ReelIntel backend.
All values are read from environment variables with sensible defaults.
Create a .env file in the project root to override any of these.
"""

import os
from pathlib import Path

APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

# ── Directories ────────────────────────────────────────────────────────────────
# Base dir for temporary downloads (relative to backend root)
BASE_DIR: str = os.getenv("REELAI_DOWNLOADS_DIR", "downloads")

# ── Server ────────────────────────────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ── Whisper (Speech-to-Text) ──────────────────────────────────────────────────
# Options: tiny, base, small, medium, large
WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")

# ── EasyOCR ───────────────────────────────────────────────────────────────────
# Comma-separated language codes e.g. "en,hi" for English + Hindi
OCR_LANGUAGES: list[str] = os.getenv("OCR_LANGUAGES", "en").split(",")
# Confidence threshold 0.0–1.0; texts below this are discarded
OCR_CONFIDENCE_THRESHOLD: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.4"))

# ── Frame Extraction ──────────────────────────────────────────────────────────
# Extract one frame every N seconds from the video
FRAME_INTERVAL_SEC: int = int(os.getenv("FRAME_INTERVAL_SEC", "2"))

# ── Audio Extraction ──────────────────────────────────────────────────────────
AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))

# ── Groq (LLM) ────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
# Available Groq models: llama-3.1-8b-instant, llama-3.1-70b-versatile, mixtral-8x7b-32768
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0"))
LLM_MAX_CONTEXT_CHARS: int = int(os.getenv("LLM_MAX_CONTEXT_CHARS", "8000"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "512"))

# ── Serper (Web Search) ───────────────────────────────────────────────────────
SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
SERPER_API_URL: str = os.getenv("SERPER_API_URL", "https://google.serper.dev/search")
# Number of search results to return
SEARCH_NUM_RESULTS: int = int(os.getenv("SEARCH_NUM_RESULTS", "10"))

# ── Device ────────────────────────────────────────────────────────────────────
# auto = use CUDA if available, else CPU
# force values: "cuda" or "cpu"
DEVICE_PREFERENCE: str = os.getenv("DEVICE_PREFERENCE", "auto")

# ── Cleanup ───────────────────────────────────────────────────────────────────
# Whether to delete downloaded video/audio/frames after processing
CLEANUP_AFTER_PROCESSING: bool = os.getenv("CLEANUP_AFTER_PROCESSING", "true").lower() == "true"

# ── CORS ──────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed origins. Use "*" for all (dev only).
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
