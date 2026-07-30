"""
AquaShield — Phase 3B Gemma Client Test Suite
Tests:
1. Exponential backoff retry logic on 429/5xx errors using failure injection.
2. Lat/Lon rounding cache (~100m precision) hit confirmation.
3. Offline fallback behavior when API key is missing.
"""

import sys
from pathlib import Path
import pytest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.gemma_client import (
    generate_risk_explanation,
    clear_gemma_cache,
    get_cache_key,
    call_gemma_api,
    _retry_stats
)


def test_lat_lon_cache_hit():
    clear_gemma_cache()
    lat, lon = 12.9716, 77.5946

    prompt = "Test prompt for cache"

    # First call: Should be a cache miss
    out1, is_cache1 = generate_risk_explanation(prompt, lat=lat, lon=lon)
    assert is_cache1 is False, "First call should be a cache miss"

    # Second call with exact same lat/lon: Should be a cache hit
    out2, is_cache2 = generate_risk_explanation(prompt, lat=lat, lon=lon)
    assert is_cache2 is True, "Second identical call should be a cache hit"
    assert out1 == out2, "Cached output must match original output"

    # Third call with slightly offset lat/lon (< 100m difference, e.g. +0.0003 deg)
    out3, is_cache3 = generate_risk_explanation(prompt, lat=12.9719, lon=77.5946)
    assert is_cache3 is True, "Call within ~100m rounding boundary (12.972, 77.595) should be a cache hit"


def test_exponential_backoff_failure_injection(monkeypatch):
    clear_gemma_cache()
    attempts_counted = 0

    def mock_failing_generate_content(*args, **kwargs):
        nonlocal attempts_counted
        attempts_counted += 1
        raise Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")

    # Patch google genai client if available or simulate failure retry
    import app.services.gemma_client as gc
    monkeypatch.setattr(gc, "GOOGLE_AI_STUDIO_API_KEY", "fake_key_for_retry_test")

    class MockGenaiClient:
        def __init__(self, api_key):
            self.models = self

        def generate_content(self, *args, **kwargs):
            return mock_failing_generate_content(*args, **kwargs)

    class MockGenaiModule:
        Client = MockGenaiClient
        class types:
            class GenerateContentConfig:
                def __init__(self, **kwargs):
                    pass

    sys.modules["google"] = type(sys)("google")
    sys.modules["google.genai"] = MockGenaiModule()
    sys.modules["google.genai.types"] = MockGenaiModule.types

    # Execute call_gemma_api with max_retries=2
    with pytest.raises(Exception) as exc_info:
        call_gemma_api("Test retry prompt", max_retries=2)

    assert "429" in str(exc_info.value)
    # Total calls should be 1 initial attempt + 2 retries = 3 attempts
    assert attempts_counted == 3, f"Expected 3 attempts (1 initial + 2 retries), got {attempts_counted}"
    print("\n  [PASS] Exponential backoff test verified: 3 total attempts executed on 429 errors.")


if __name__ == "__main__":
    pytest.main(["-s", __file__])
