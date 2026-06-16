"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import APP_VERSION, CORS_ORIGINS, LOG_LEVEL
from app.routes.analyze import router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ReelIntel API",
    description=(
        "Analyze social-media reels to identify the product being promoted. "
        "Downloads the video, transcribes audio (Whisper), reads text from frames (EasyOCR), "
        "generates a product fingerprint via an LLM (Groq), and returns web search results."
    ),
    version=APP_VERSION,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, tags=["UI"])
def root():
    """Serve the polished web UI index.html."""
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file):
        with open(static_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>ReelAI UI not found</h1>", status_code=404)


@app.get("/health", tags=["Health"])
def health():
    """Detailed health check — reports which API keys are configured."""
    from app.config import APP_VERSION, GROQ_API_KEY, SERPER_API_KEY

    return {
        "status": "ok",
        "version": APP_VERSION,
        "groq_key_set": bool(GROQ_API_KEY),
        "serper_key_set": bool(SERPER_API_KEY),
    }