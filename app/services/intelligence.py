"""LLM-powered product fingerprinting via Groq API."""

from __future__ import annotations

import json
import logging
import re

from app.config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, LLM_MAX_CONTEXT_CHARS, LLM_MAX_TOKENS

logger = logging.getLogger(__name__)

# System prompt — kept as a constant to avoid re-definition on each call.
_SYSTEM_PROMPT = (
    "You analyze product promotions from social-media reels and return structured JSON. "
    "Be concise and specific. Return only valid JSON — no markdown, no extra text."
)

_USER_PROMPT_TEMPLATE = """\
You are analyzing a reel promoting a product or service.

Context clues may mention export platforms (e.g. Lovable, V0, Cursor, Webflow, etc.).
Those are destination tools — NOT the main product being promoted.

Identify the MAIN product being advertised.

Focus on:
- What website / tool the viewer is directed to visit
- What that tool actually does for the user
- What makes it different from generic AI builders

Extract these fields:

1. main_product_role        – What it actually is (very specific, 1–2 sentences)
2. core_mechanism           – How it works mechanically (e.g. "prompt → template → export")
3. business_model_hint      – Monetization hint (free tier? marketplace? subscription?)
4. export_targets           – List of platforms outputs are sent to (e.g. ["Lovable", "Cursor"])
5. distinctive_visual_clues – Memorable visual elements from the reel
6. rare_or_brand_like_terms_from_ocr – Unusual or branded words seen on screen

Return ONLY this JSON (no markdown fences):
{{
  "main_product_role": "",
  "core_mechanism": "",
  "business_model_hint": "",
  "export_targets": [],
  "distinctive_visual_clues": [],
  "rare_or_brand_like_terms_from_ocr": []
}}

Content from reel:
{full_text}
"""


def _get_client():
    """Return a Groq client; raise clearly if key is missing."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://console.groq.com"
        )
    from groq import Groq  # type: ignore[import]

    return Groq(api_key=GROQ_API_KEY)


def build_fingerprint(full_text: str) -> dict:
    """
    Send reel text to Groq and parse the product fingerprint JSON.

    Args:
        full_text: Combined transcript + OCR text from the reel.

    Returns:
        Parsed fingerprint dict, or {} if parsing fails.
    """
    if not full_text.strip():
        logger.info("[Intelligence] Empty text — skipping LLM call.")
        return {}

    client = _get_client()
    prompt = _USER_PROMPT_TEMPLATE.format(full_text=full_text[:LLM_MAX_CONTEXT_CHARS])  # stay within context window

    logger.info(f"[Intelligence] Calling Groq ({GROQ_MODEL})…")
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=GROQ_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    raw: str = response.choices[0].message.content.strip()
    logger.info(f"[Intelligence] Raw response ({len(raw)} chars): {raw[:200]}…")

    # Extract JSON block from response (model sometimes wraps in backticks)
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        logger.info("[Intelligence] No JSON object found in response.")
        return {}

    try:
        return json.loads(json_match.group(0))
    except json.JSONDecodeError as exc:
        logger.info(f"[Intelligence] JSON parse error: {exc}")
        return {}