"""Web search via Serper.dev (Google Search API)."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

from app.config import SEARCH_NUM_RESULTS, SERPER_API_KEY, SERPER_API_URL


def build_search_query(fingerprint: dict) -> str:
    """
    Convert a product fingerprint into a focused Google search query.
    Pulls the most informative fields and appends "official website".
    """
    parts: list[str] = []

    core = (
        fingerprint.get("core_mechanism")
        or fingerprint.get("main_product_role")
        or ""
    ).strip()
    if core:
        parts.append(core)

    for term in fingerprint.get("rare_or_brand_like_terms_from_ocr", []):
        t = str(term).strip()
        if t:
            parts.append(t)

    for clue in fingerprint.get("distinctive_visual_clues", []):
        c = str(clue).strip()
        if c:
            parts.append(c)

    if not parts:
        # Fallback: use whatever we have
        parts.append(fingerprint.get("main_product_role", ""))

    parts.append("official website")
    return " ".join(p for p in parts if p).strip()


def search_web(query: str, num_results: int | None = None) -> list[dict]:
    """
    Search Google via Serper.dev and return organic results.

    Args:
        query:       The search string.
        num_results: Override the default number of results.

    Returns:
        List of dicts with keys: title, link, snippet.

    Raises:
        RuntimeError: If SERPER_API_KEY is missing or the API call fails.
    """
    if not SERPER_API_KEY:
        raise RuntimeError(
            "SERPER_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://serper.dev (100 free searches/month)."
        )

    n = num_results if num_results is not None else SEARCH_NUM_RESULTS

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": n}

    logger.info(f"[Retriever] Searching: {query!r} (n={n})")
    response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(
            f"Serper API returned HTTP {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    results: list[dict] = []
    for item in data.get("organic", []):
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
        )

    logger.info(f"[Retriever] Got {len(results)} result(s).")
    return results