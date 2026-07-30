"""Comprehensive pytest suite for Guardrail Core service."""

import pytest
from app.services.guardrail import (
    clean_response,
    compute_trust_score,
    extract_claims,
    match_indicator,
    verify,
    verify_claims,
)
from app.services.models import Claim, ClaimType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_payload_flat():
    """Flat sample payload fixture."""
    return {
        "surface_water": -12.4,
        "flood": "moderate",
        "rainfall": None,
    }


@pytest.fixture
def sample_payload_nested():
    """Nested payload fixture matching Blueprint specification."""
    return {
        "indicators": {
            "surface_water_trend": {
                "value": -12.4,
                "unit": "% change 10yr",
                "source": "GEE/JRC-GSW",
                "confidence": "measured",
            },
            "flood_exposure": {
                "value": "moderate",
                "source": "GEE/flood-layer",
                "confidence": "measured",
            },
            "rainfall_proxy": {
                "value": None,
                "source": None,
                "confidence": "no_data",
            },
        }
    }


# ---------------------------------------------------------------------------
# Required Minimum Tests
# ---------------------------------------------------------------------------
def test_fully_grounded(sample_payload_flat):
    """Test fully grounded response where all claims match payload."""
    text = "Surface water declined by 12.4%. Flood exposure is moderate."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 2
    assert result["claims_grounded"] == 2
    assert result["claims_rejected"] == 0
    assert result["trust_score"] == 1.0
    assert len(result["rejected_claims"]) == 0
    assert "~~" not in result["clean_text"]


def test_partially_grounded(sample_payload_flat):
    """Test response with grounded facts and an unsupported claim (prompt example)."""
    text = "Surface water declined by 12.4%. Flood exposure is moderate. Rainfall declined by 35%."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 3
    assert result["claims_grounded"] == 2
    assert result["claims_rejected"] == 1
    assert result["trust_score"] == 0.67
    assert len(result["rejected_claims"]) == 1
    assert "~~Rainfall declined by 35%.~~ Removed — Unverifiable" in result["clean_text"]


def test_fully_hallucinated(sample_payload_flat):
    """Test response with entirely hallucinated/unsupported claims."""
    text = "Surface water increased by 99%. Flood exposure is severe. Rainfall dropped 80%."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 3
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 3
    assert result["trust_score"] == 0.0
    assert len(result["rejected_claims"]) == 3
    assert "Removed — Unverifiable" in result["clean_text"]


def test_null_indicator(sample_payload_flat):
    """Test that indicator with null value in payload is rejected."""
    text = "Rainfall declined by 35%."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1
    assert result["trust_score"] == 0.0
    assert "null" in result["rejected_claims"][0].lower()


def test_wrong_categorical_value(sample_payload_flat):
    """Test categorical mismatch rejection."""
    text = "Flood exposure is high."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1
    assert "does not match payload value" in result["rejected_claims"][0]


def test_empty_response(sample_payload_flat):
    """Test graceful handling of empty or None response text."""
    result_empty = verify("", sample_payload_flat)
    assert result_empty["clean_text"] == ""
    assert result_empty["claims_checked"] == 0
    assert result_empty["trust_score"] == 1.0

    result_none = verify(None, sample_payload_flat)
    assert result_none["clean_text"] == ""
    assert result_none["claims_checked"] == 0
    assert result_none["trust_score"] == 1.0


def test_malformed_payload():
    """Test graceful handling of missing, None, or malformed payload."""
    text = "Surface water declined by 12.4%."

    result_none = verify(text, None)
    assert result_none["claims_checked"] == 1
    assert result_none["claims_grounded"] == 0
    assert result_none["claims_rejected"] == 1
    assert result_none["trust_score"] == 0.0

    result_malformed = verify(text, "not_a_dict")  # type: ignore
    assert result_malformed["claims_checked"] == 1
    assert result_malformed["claims_grounded"] == 0
    assert result_malformed["claims_rejected"] == 1


def test_alias_matching():
    """Test alias resolution for various indicator name variants."""
    assert match_indicator("water trend") == "surface_water_trend"
    assert match_indicator("surface water") == "surface_water_trend"
    assert match_indicator("flood risk") == "flood_exposure"
    assert match_indicator("precipitation") == "rainfall_proxy"
    assert match_indicator("unknown indicator xyz") is None


# ---------------------------------------------------------------------------
# Additional Edge Case & Unit Tests
# ---------------------------------------------------------------------------
def test_nested_indicators_payload(sample_payload_nested):
    """Test support for nested Blueprint indicator payload structures."""
    text = "Surface water declined by 12.4%. Flood exposure is moderate."
    result = verify(text, sample_payload_nested)

    assert result["claims_checked"] == 2
    assert result["claims_grounded"] == 2
    assert result["trust_score"] == 1.0


def test_mixed_clause_claims(sample_payload_flat):
    """Test mixed sentence containing supported and unsupported clauses."""
    text = "Flood exposure is moderate because rainfall dropped 35%."
    result = verify(text, sample_payload_flat)

    assert result["claims_checked"] == 2
    assert result["claims_grounded"] == 1
    assert result["claims_rejected"] == 1
    assert result["trust_score"] == 0.5
    assert "~~" in result["clean_text"]
    assert "Removed — Unverifiable" in result["clean_text"]



def test_extract_claims_helper():
    """Unit test for extract_claims function."""
    claims = extract_claims("Surface water declined by 12.4%. Flood exposure is moderate.")
    assert len(claims) == 2
    assert claims[0].claim_type == ClaimType.NUMERIC
    assert claims[0].extracted_number == 12.4
    assert claims[1].claim_type == ClaimType.CATEGORICAL
    assert claims[1].extracted_category == "moderate"


def test_compute_trust_score_helper():
    """Unit test for compute_trust_score formula and edge cases."""
    assert compute_trust_score(0, 0)["trust_score"] == 1.0
    assert compute_trust_score(4, 3)["trust_score"] == 0.75
    assert compute_trust_score(3, 1)["trust_score"] == 0.33
    assert compute_trust_score(2, 0)["trust_score"] == 0.0


def test_unsupported_indicator_claim(sample_payload_flat):
    """Test claim with unrecognized indicator is rejected."""
    text = "Temperature rose by 40 degrees."
    result = verify(text, sample_payload_flat)
    assert result["claims_checked"] == 1
    assert result["claims_rejected"] == 1
    assert "unsupported" in result["rejected_claims"][0].lower() or "unrecognized" in result["rejected_claims"][0].lower() or "not found" in result["rejected_claims"][0].lower()


def test_non_numeric_payload_value():
    """Test numeric claim against non-numeric payload value."""
    payload = {"surface_water": "invalid_non_numeric"}
    text = "Surface water declined by 12.4%."
    result = verify(text, payload)
    assert result["claims_rejected"] == 1
    assert "not numeric" in result["rejected_claims"][0]


def test_verify_claims_invalid_input():
    """Test verify_claims directly with non-list claims input."""
    assert verify_claims("not_a_list", {}) == []  # type: ignore


def test_exception_fallback_in_verify(monkeypatch):
    """Test that master verify API catches unexpected exceptions gracefully without crashing."""
    def bad_extract_claims(text):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr("app.services.guardrail.extract_claims", bad_extract_claims)
    result = verify("Some response text", {"surface_water": -12.4})
    assert result["trust_score"] == 0.0
    assert "Verification error" in result["rejected_claims"][0]

