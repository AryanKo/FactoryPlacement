"""Comprehensive pytest suite for Guardrail Core service."""

import random

import pytest
from app.services.guardrail import (
    compute_trust_score,
    extract_claims,
    match_indicator,
    verify,
    verify_claims,
)
from app.services.models import ClaimType


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
    assert compute_trust_score(3, 5) == {
        "claims_checked": 3,
        "claims_grounded": 3,
        "claims_rejected": 0,
        "trust_score": 1.0,
    }
    assert compute_trust_score(-1, 2) == {
        "claims_checked": 0,
        "claims_grounded": 0,
        "claims_rejected": 0,
        "trust_score": 1.0,
    }


def test_unsupported_indicator_claim(sample_payload_flat):
    """Test claim with unrecognized indicator is rejected."""
    text = "Temperature rose by 40 degrees."
    result = verify(text, sample_payload_flat)
    assert result["claims_checked"] == 1
    assert result["claims_rejected"] == 1
    rejected_claim = result["rejected_claims"][0].lower()
    assert (
        "unsupported" in rejected_claim
        or "unrecognized" in rejected_claim
        or "not found" in rejected_claim
    )


def test_non_numeric_payload_value():
    """Test numeric claim against non-numeric payload value."""
    payload = {"surface_water": "invalid_non_numeric"}
    text = "Surface water declined by 12.4%."
    result = verify(text, payload)
    assert result["claims_rejected"] == 1
    assert "not numeric" in result["rejected_claims"][0]


def test_negative_numeric_direction_does_not_verify_as_increase(sample_payload_flat):
    """Positive directional claims should not match negative trend payloads."""
    result = verify("Surface water increased by 12.4%.", sample_payload_flat)

    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1
    assert "does not match payload value" in result["rejected_claims"][0]


def test_sign_mismatch_without_direction_is_rejected():
    """Absolute values must not hide a sign mismatch in a neutral claim."""
    result = verify("Surface water is 12.4%.", {"surface_water": -12.4})
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1


def test_nested_unknown_indicator_key_matches_payload():
    """Nested payload keys should be available for non-canonical indicators."""
    payload = {"indicators": {"custom_metric": {"value": 5}}}
    result = verify("Custom metric is 5.", payload)

    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 1
    assert result["claims_rejected"] == 0


def test_verify_claims_invalid_input():
    """Test verify_claims directly with non-list claims input."""
    assert verify_claims("not_a_list", {}) == []  # type: ignore


def test_exception_fallback_in_verify(monkeypatch):
    """Test that verifier errors fail closed without leaking raw output or details."""
    def bad_extract_claims(text):
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr("app.services.guardrail.extract_claims", bad_extract_claims)
    result = verify("Some response text", {"surface_water": -12.4})
    assert result["clean_text"] == ""
    assert result["trust_score"] == 0.0
    assert result["rejected_claims"] == ["Verification error"]


def test_alias_matching_requires_word_boundaries():
    """Unrelated words must not trigger indicator aliases."""
    assert match_indicator("train speed is 12") is None
    assert match_indicator("notaflood condition") is None
    assert match_indicator("flooding is widespread") is None


def test_alias_matching_tolerates_extra_whitespace():
    """Whitespace variation should not disable known aliases."""
    assert match_indicator("Surface   Water declined") == "surface_water_trend"


def test_indicator_only_claim_is_rejected(sample_payload_flat):
    """Mentioning an indicator without a value is not grounded evidence."""
    result = verify(
        "The word contains precipitation-like text.",
        {"rainfall": 35},
    )
    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1
    assert "no verifiable" in result["rejected_claims"][0]


def test_negated_category_is_rejected(sample_payload_flat):
    """A negated category must not verify as a positive assertion."""
    result = verify("Flood exposure is not moderate.", sample_payload_flat)
    assert result["claims_checked"] == 1
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1


def test_categorical_matching_is_exact():
    """Similar category strings must not pass by substring containment."""
    result = verify("Flood exposure is high.", {"flood_exposure": "very high"})
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1


def test_categorical_whitespace_variant_matches():
    """Whitespace and underscore forms of no-data should compare equally."""
    result = verify("Rainfall has no data.", {"rainfall": "no_data"})
    assert result["claims_grounded"] == 1
    assert result["claims_rejected"] == 0


def test_numeric_formats_are_parsed_correctly():
    """Decimal, comma-formatted, and scientific values should remain intact."""
    assert extract_claims("Surface water declined by .5%.")[0].extracted_number == 0.5
    assert (
        extract_claims("Surface water declined by 1,234.5%.")[0].extracted_number
        == 1234.5
    )
    assert (
        extract_claims("Surface water declined by 1.2e3%.")[0].extracted_number
        == 1200.0
    )


def test_multiple_numeric_values_are_rejected_as_ambiguous():
    """A claim must not pass by validating only its first numeric value."""
    result = verify(
        "Surface water changed from 10% to 12.4%.",
        {"surface_water": -10},
    )
    assert result["claims_grounded"] == 0
    assert result["claims_rejected"] == 1
    assert "multiple numeric values" in result["rejected_claims"][0]


def test_unicode_sentence_boundaries_are_supported(sample_payload_flat):
    """Unicode sentence punctuation should separate adjacent claims."""
    result = verify(
        "Surface water declined by 12.4%。Flood exposure is moderate！",
        sample_payload_flat,
    )
    assert result["claims_checked"] == 2
    assert result["claims_grounded"] == 2


def test_duplicate_rejected_claims_are_all_struck(sample_payload_flat):
    """Each repeated rejected assertion should be marked independently."""
    result = verify(
        "Surface water increased by 99%. Surface water increased by 99%.",
        sample_payload_flat,
    )
    assert result["claims_rejected"] == 2
    assert result["clean_text"].count("Removed — Unverifiable") == 2


def test_randomized_inputs_are_safe_and_deterministic():
    """Randomized text and payloads must never crash or produce unstable output."""
    rng = random.Random(20260730)
    alphabet = "abcXYZ012!?,.; _-\n\t😀流域"
    values = [None, "", 0, -0.0, 1, -12.4, 12.4, "low", "moderate", [], {}, True]

    for _ in range(100):
        response = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 250)))
        payload = {
            "indicators": {
                rng.choice(
                    [
                        "surface_water_trend",
                        "flood_exposure",
                        "rainfall_proxy",
                        "custom_metric",
                    ]
                ): rng.choice(values)
            }
        }
        first = verify(response, payload)
        second = verify(response, payload)
        assert first == second


@pytest.mark.parametrize(
    "response",
    [None, 1, -1, 1.5, [], (), {}, b"bytes", "😀流域—−", "x" * 10000],
)
def test_untrusted_response_types_do_not_crash(response):
    """The public API must tolerate non-string and oversized response inputs."""
    result = verify(response, {"surface_water": -12.4})
    assert set(result) == {
        "clean_text",
        "claims_checked",
        "claims_grounded",
        "claims_rejected",
        "trust_score",
        "rejected_claims",
    }


def test_deeply_nested_payload_does_not_crash():
    """Unexpected nesting should be rejected or ignored without exceptions."""
    value = -12.4
    for _ in range(100):
        value = {"nested": value}

    result = verify(
        "Surface water declined by 12.4%.",
        {"indicators": {"surface_water_trend": value}},
    )
    assert result["claims_rejected"] == 1
