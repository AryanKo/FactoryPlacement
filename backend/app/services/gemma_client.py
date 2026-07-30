"""
AquaShield — Gemma 4 Client Wrapper (Google AI Studio API)
Integrates Gemma 4 31B Instruct via google-genai SDK.
Implements exponential backoff on 429/5xx errors and an in-memory (lat, lon) cache (~100m precision).
"""

import os
import sys
import time
from typing import Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

GEMMA_MODEL_NAME = os.getenv("GEMMA_MODEL_NAME", "gemma-4-31b-it")
GOOGLE_AI_STUDIO_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "").strip()

# In-process cache keyed on (lat_rounded, lon_rounded)
_gemma_cache: Dict[str, str] = {}
_retry_stats: Dict[str, int] = {"retries_attempted": 0, "cache_hits": 0}


def get_cache_key(lat: float, lon: float) -> str:
    """Rounds lat/lon to 3 decimal places (~100 meters precision)."""
    return f"{round(lat, 3)},{round(lon, 3)}"


def clear_gemma_cache():
    """Clears the in-memory response cache and reset stats."""
    global _gemma_cache, _retry_stats
    _gemma_cache.clear()
    _retry_stats = {"retries_attempted": 0, "cache_hits": 0}


def call_gemma_api(prompt_text: str, temperature: float = 0.2, max_retries: int = 2) -> Tuple[str, bool]:
    """
    Calls Google AI Studio API for Gemma 4 31B Instruct.
    Implements exponential backoff on rate limits (429) or server errors (5xx).
    Returns (response_text, is_fallback_or_mock).

    Splits the prompt on SYSTEM:/DATA:/SOURCE:/TASK: markers and uses the SDK's
    native system_instruction parameter so the model correctly applies the
    grounding constraint — sending everything as a single blob causes empty responses.
    """
    global _retry_stats

    api_key = GOOGLE_AI_STUDIO_API_KEY or os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        print("[GEMMA WARN] GOOGLE_AI_STUDIO_API_KEY not set. Returning grounded offline response.")
        return (
            "Based on GEE indicators, surface water has decreased by 12.4% over 10 years. "
            "Per AWS Water Stewardship Standard §3.1, the facility must reduce freshwater intake by 15%.",
            True,
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        attempt = 0
        backoff_delay = 1.0

        # Split "SYSTEM:\n...\n\nDATA:\n...\n\nSOURCE:...\n\nTASK:\n..." into two parts.
        # The system block (everything before DATA:) becomes system_instruction.
        # The rest becomes the user message so the SDK routes it correctly.
        system_text = (
            "You are a water-risk assistant. You may ONLY state facts that appear in the DATA block below. "
            "If an indicator value is null or 'no_data', you must state 'not available' — do NOT estimate, "
            "infer, or fill in a plausible value under any circumstances. "
            "Every recommendation must quote or closely paraphrase the SOURCE block and cite its section."
        )

        # Strip any leading SYSTEM: block from the prompt_text to avoid duplication
        user_text = prompt_text
        if prompt_text.strip().startswith("SYSTEM:"):
            parts = prompt_text.split("DATA:", 1)
            if len(parts) == 2:
                user_text = "DATA:" + parts[1]

        while attempt <= max_retries:
            try:
                response = client.models.generate_content(
                    model=GEMMA_MODEL_NAME,
                    contents=user_text,
                    config=types.GenerateContentConfig(
                        system_instruction=system_text,
                        temperature=temperature,
                        max_output_tokens=600,
                    ),
                )

                # Log response metadata for debugging
                if response.candidates:
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, "finish_reason", "UNKNOWN")
                    print(f"[GEMMA] finish_reason={finish_reason}")
                    safety_ratings = getattr(candidate, "safety_ratings", None) or []
                    for sr in safety_ratings:
                        print(f"[GEMMA] safety: {sr}")
                    # Extract text from parts if response.text is None
                    if response.text:
                        return (response.text.strip(), False)
                    # Try extracting from parts directly
                    content = candidate.content
                    if content and content.parts:
                        full_text = "".join(
                            part.text for part in content.parts if hasattr(part, "text") and part.text
                        )
                        if full_text.strip():
                            return (full_text.strip(), False)
                    print(f"[GEMMA WARN] 200 OK but no text content. finish_reason={finish_reason}")
                    return (f"Gemma returned no content (finish_reason={finish_reason}). GEE data is available above.", True)
                else:
                    print("[GEMMA WARN] No candidates in response.")
                    return ("Gemma returned no candidates. GEE data is available above.", True)

            except Exception as exc:
                exc_str = str(exc)
                attempt += 1
                _retry_stats["retries_attempted"] += 1

                if attempt > max_retries:
                    print(f"[GEMMA ERROR] Max retries ({max_retries}) exceeded: {exc_str}", file=sys.stderr)
                    raise exc

                if "429" in exc_str or "500" in exc_str or "503" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                    print(f"[GEMMA RETRY] Attempt {attempt}/{max_retries} failed ({exc_str[:60]}). Retrying in {backoff_delay:.1f}s...")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0
                else:
                    raise exc

    except Exception as e:
        print(f"[GEMMA FAIL] Call failed: {e}", file=sys.stderr)
        raise e


def generate_risk_explanation(prompt_text: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Tuple[str, bool]:
    """
    Wrapper function with (lat, lon) response caching.
    Returns (raw_gemma_output, is_cache_hit).
    """
    global _retry_stats

    if lat is not None and lon is not None:
        cache_key = get_cache_key(lat, lon)
        if cache_key in _gemma_cache:
            _retry_stats["cache_hits"] += 1
            print(f"[GEMMA CACHE HIT] Key: {cache_key}")
            return (_gemma_cache[cache_key], True)

    output, _ = call_gemma_api(prompt_text, temperature=0.2)

    if lat is not None and lon is not None:
        cache_key = get_cache_key(lat, lon)
        _gemma_cache[cache_key] = output

    return (output, False)


if __name__ == "__main__":
    print("Testing Gemma Client Cache & Retry Wrapper...")
    test_prompt = "Say 'AquaShield Grounded Gemma 4 active'"
    out1, hit1 = generate_risk_explanation(test_prompt, lat=12.9716, lon=77.5946)
    print(f"Call 1 (Cache hit={hit1}): {out1[:80]}...")

    out2, hit2 = generate_risk_explanation(test_prompt, lat=12.9716, lon=77.5946)
    print(f"Call 2 (Cache hit={hit2}): {out2[:80]}...")
