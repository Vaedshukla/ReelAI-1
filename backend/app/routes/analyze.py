"""POST /analyze — main ReelIntel pipeline endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator

from app.services import extractor
from app.services.intelligence import build_fingerprint
from app.services.retriever import build_search_query, search_web
from app.services.vision import analyze_frames

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url must not be empty")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class AnalyzeResponse(BaseModel):
    url: str
    transcript: str
    visual_text: str
    fingerprint: dict
    search_query: str
    candidates: list[dict]


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_reel(body: AnalyzeRequest) -> dict:
    """
    Full ReelIntel pipeline:
    1. Download reel → 2. Transcribe audio → 3. OCR frames
    4. LLM fingerprint → 5. Web search → return results
    """
    url = body.url
    logger.info("Starting analysis for: %s", url)

    # ── Step 1–3: Extract transcript + visual text ────────────────────────────
    try:
        extracted = extractor.extract(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected extraction error")
        raise HTTPException(status_code=500, detail="Video extraction failed. Check server logs.") from exc

    transcript: str = extracted.get("transcript", "")
    frames_dir: str = extracted.get("frames_dir", "")

    # frames_dir may have been cleaned up already if CLEANUP_AFTER_PROCESSING=true
    # analyze_frames handles missing dirs gracefully.
    try:
        visual_text: str = analyze_frames(frames_dir)
    except Exception as exc:
        logger.warning("OCR failed (non-fatal): %s", exc)
        visual_text = ""

    full_text = f"{transcript} {visual_text}".strip()

    # ── Step 4: LLM fingerprint ───────────────────────────────────────────────
    try:
        fingerprint = build_fingerprint(full_text)
    except RuntimeError as exc:
        # Missing API key → tell the user clearly
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("Fingerprint failed (non-fatal): %s", exc)
        fingerprint = {}

    # ── Step 5: Web search ────────────────────────────────────────────────────
    query = build_search_query(fingerprint) if fingerprint else transcript[:120]
    logger.info("Search query: %s", query)

    try:
        candidates = search_web(query)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("Search failed (non-fatal): %s", exc)
        candidates = []

    return {
        "url": url,
        "transcript": transcript,
        "visual_text": visual_text,
        "fingerprint": fingerprint,
        "search_query": query,
        "candidates": candidates,
    }
