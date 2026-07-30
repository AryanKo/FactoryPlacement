"""Guardrail Core service for AquaShield.

Deterministic verification engine ensuring model output is strictly grounded
in Earth Engine structured payloads.
"""
import re
from typing import Any, Dict, List, Optional
from app.services.models import Claim, ClaimType, GuardrailResult, VerifiedClaim


INDICATOR_ALIASES: Dict[str, List[str]] = {
    "surface_water_trend": [
        "surface water trend",
        "surface water",
        "water trend",
        "water level",
        "surface_water",
        "surface_water_trend",
        "water loss",
        "water decline",
        "water gain",
    ],
    "flood_exposure": [
        "flood exposure",
        "flood risk",
        "flood hazard",
        "flood",
        "flood_exposure",
        "flood_risk",
    ],
    "rainfall_proxy": [
        "rainfall proxy",
        "rainfall",
        "rain",
        "precipitation",
        "rainfall_proxy",
        "rain proxy",
    ],
}

CATEGORICAL_KEYWORDS = {
    "low",
    "moderate",
    "high",
    "very high",
    "severe",
    "extreme",
    "stable",
    "increasing",
    "decreasing",
    "measured",
    "no_data",
    "none",
}


def match_indicator(claim_or_text: Any, payload_keys: Optional[List[str]] = None) -> Optional[str]:
    """Determine which indicator an extracted claim or text string references.

    Supports custom payload keys and extensible alias mappings.
    """
    if not claim_or_text:
        return None

    text = claim_or_text.text if hasattr(claim_or_text, "text") else str(claim_or_text)
    text_lower = text.lower()

    # 1. Check against payload_keys if provided
    if payload_keys:
        for key in payload_keys:
            key_lower = key.lower()
            key_spaced = key_lower.replace("_", " ")
            if key_lower in text_lower or key_spaced in text_lower:
                return key

    # 2. Check predefined aliases (longest match first)
    for canonical_name, aliases in INDICATOR_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if alias.lower() in text_lower:
                return canonical_name

    return None


def extract_number_from_text(text: str) -> Optional[float]:
    """Extract numeric value from text, handling negative numbers and percentages."""
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def extract_category_from_text(text: str) -> Optional[str]:
    """Extract categorical risk or status value from text."""
    text_lower = text.lower()
    for cat in sorted(CATEGORICAL_KEYWORDS, key=len, reverse=True):
        pattern = r"\b" + re.escape(cat) + r"\b"
        if re.search(pattern, text_lower):
            return cat
    return None


def split_sentences(text: str) -> List[str]:
    """Split text into sentences cleanly while preserving structure."""
    if not text:
        return []
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in raw_sentences if s.strip()]


def split_clauses_if_mixed(sentence: str) -> List[str]:
    """Split sentence into sub-clauses if it contains multiple distinct factual assertions."""
    clause_delimiters = r"\b(?:because|and|while|but|whereas)\b|;"
    parts = re.split(clause_delimiters, sentence, flags=re.IGNORECASE)
    cleaned_parts = [p.strip() for p in parts if p.strip()]

    if len(cleaned_parts) > 1:
        indicators = [match_indicator(p) for p in cleaned_parts]
        valid_indicators = [ind for ind in indicators if ind is not None]
        has_numbers = any(extract_number_from_text(p) is not None for p in cleaned_parts)
        if len(set(valid_indicators)) > 1 or (len(valid_indicators) >= 1 and has_numbers):
            return cleaned_parts

    return [sentence]


def extract_claims(text: Optional[str]) -> List[Claim]:
    """Extract factual claims (numeric, categorical, mixed) from response text."""
    if not text or not isinstance(text, str):
        return []

    claims: List[Claim] = []
    sentences = split_sentences(text)

    for sentence in sentences:
        clauses = split_clauses_if_mixed(sentence)
        for clause in clauses:
            indicator = match_indicator(clause)
            number = extract_number_from_text(clause)
            category = extract_category_from_text(clause)

            # Ignore text with no numeric/categorical assertions or indicator keywords
            if indicator is None and number is None and category is None:
                continue

            if number is not None and category is not None:
                claim_type = ClaimType.MIXED
            elif number is not None:
                claim_type = ClaimType.NUMERIC
            elif category is not None:
                claim_type = ClaimType.CATEGORICAL
            else:
                claim_type = ClaimType.UNKNOWN

            claim = Claim(
                text=clause,
                original_sentence=sentence,
                claim_type=claim_type,
                indicator_alias=indicator,
                extracted_number=number,
                extracted_category=category,
            )
            claims.append(claim)

    return claims


def get_indicator_payload_entry(payload: Any, indicator_key: Optional[str]) -> tuple[bool, Any]:
    """Retrieve value for an indicator from flat or nested payload."""
    if not isinstance(payload, dict) or not indicator_key:
        return False, None

    # Determine dictionary containing indicators
    if "indicators" in payload and isinstance(payload["indicators"], dict):
        search_dict = payload["indicators"]
    else:
        search_dict = payload

    # 1. Direct match
    if indicator_key in search_dict:
        val = search_dict[indicator_key]
        if isinstance(val, dict) and "value" in val:
            return True, val["value"]
        return True, val

    # 2. Key match via known aliases
    aliases = INDICATOR_ALIASES.get(indicator_key, [indicator_key])
    for alias in aliases:
        # Check underscore version and spaced version
        alias_underscore = alias.lower().replace(" ", "_")
        for key in search_dict.keys():
            key_normalized = key.lower().replace(" ", "_")
            if key_normalized == alias_underscore:
                val = search_dict[key]
                if isinstance(val, dict) and "value" in val:
                    return True, val["value"]
                return True, val

    return False, None


def verify_claims(claims: List[Claim], payload: Optional[Dict[str, Any]]) -> List[VerifiedClaim]:
    """Verify claims against structured indicator payload.

    Rules:
    - Numeric values must match payload.
    - Categorical values must match payload.
    - If payload value is null -> Reject.
    - If indicator doesn't exist -> Reject.
    - If sentence contains unsupported facts -> Reject.
    """
    results: List[VerifiedClaim] = []

    if not isinstance(claims, list):
        return results

    payload_keys = list(payload.keys()) if isinstance(payload, dict) else []

    for claim in claims:
        matched_ind = claim.indicator_alias or match_indicator(claim.text, payload_keys)

        if not isinstance(payload, dict) or payload is None:
            results.append(
                VerifiedClaim(
                    claim=claim,
                    verified=False,
                    reason="Missing or malformed payload",
                    matched_indicator=matched_ind,
                    payload_value=None,
                )
            )
            continue

        if not matched_ind:
            results.append(
                VerifiedClaim(
                    claim=claim,
                    verified=False,
                    reason="Indicator unrecognized or unsupported",
                    matched_indicator=None,
                    payload_value=None,
                )
            )
            continue

        found, payload_val = get_indicator_payload_entry(payload, matched_ind)

        if not found:
            results.append(
                VerifiedClaim(
                    claim=claim,
                    verified=False,
                    reason=f"Indicator '{matched_ind}' not found in payload",
                    matched_indicator=matched_ind,
                    payload_value=None,
                )
            )
            continue

        if payload_val is None:
            results.append(
                VerifiedClaim(
                    claim=claim,
                    verified=False,
                    reason=f"Payload value for '{matched_ind}' is null",
                    matched_indicator=matched_ind,
                    payload_value=None,
                )
            )
            continue

        # Verify claim content against payload value
        is_verified = True
        reason = "Claim grounded in payload"

        if claim.extracted_number is not None:
            try:
                num_payload = float(payload_val)
                extracted_num = claim.extracted_number
                direct_match = abs(extracted_num - num_payload) < 1e-4
                abs_match = abs(abs(extracted_num) - abs(num_payload)) < 1e-4
                if not (direct_match or abs_match):
                    is_verified = False
                    reason = f"Numeric value {extracted_num} does not match payload value {payload_val}"
            except (ValueError, TypeError):
                is_verified = False
                reason = f"Payload value '{payload_val}' is not numeric"

        if is_verified and claim.extracted_category is not None:
            ext_cat = str(claim.extracted_category).strip().lower()
            pay_cat = str(payload_val).strip().lower()
            if ext_cat != pay_cat and ext_cat not in pay_cat:
                is_verified = False
                reason = f"Categorical value '{claim.extracted_category}' does not match payload value '{payload_val}'"

        results.append(
            VerifiedClaim(
                claim=claim,
                verified=is_verified,
                reason=reason,
                matched_indicator=matched_ind,
                payload_value=payload_val,
            )
        )

    return results



def clean_response(text: Optional[str], verified_claims: List[VerifiedClaim]) -> str:
    """Format original response text keeping rejected claims visible with strike-through tags.

    Format for rejected text:
    ~~rejected claim~~ Removed — Unverifiable
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text
    rejected_claims = [v for v in verified_claims if not v.verified]

    for v in rejected_claims:
        target = v.claim.text if v.claim.text in cleaned else v.claim.original_sentence
        if target and target in cleaned:
            if f"~~{target}~~" in cleaned or "Removed — Unverifiable" in target:
                continue
            replacement = f"~~{target}~~ Removed — Unverifiable"
            cleaned = cleaned.replace(target, replacement, 1)

    return cleaned



def compute_trust_score(claims_checked: int, claims_grounded: int) -> Dict[str, Any]:
    """Compute trust score stats based on checked vs grounded claims."""
    checked = max(0, claims_checked)
    grounded = max(0, claims_grounded)
    rejected = max(0, checked - grounded)
    score = round(grounded / checked, 2) if checked > 0 else 1.0
    return {
        "claims_checked": checked,
        "claims_grounded": grounded,
        "claims_rejected": rejected,
        "trust_score": score,
    }


def verify(response_text: Optional[str], payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Master API function for response verification."""
    claims = extract_claims(response_text)
    verified_results = verify_claims(claims, payload)
    grounded_count = sum(1 for v in verified_results if v.verified)
    rejected_count = sum(1 for v in verified_results if not v.verified)
    stats = compute_trust_score(len(verified_results), grounded_count)
    cleaned = clean_response(response_text, verified_results)
    rejected_claims_text = [v.claim.original_sentence for v in verified_results if not v.verified]

    result = GuardrailResult(
        clean_text=cleaned,
        claims_checked=stats["claims_checked"],
        claims_grounded=stats["claims_grounded"],
        claims_rejected=stats["claims_rejected"],
        trust_score=stats["trust_score"],
        rejected_claims=rejected_claims_text,
    )
    return result.to_dict()
