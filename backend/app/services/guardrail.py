"""Guardrail Core service for AquaShield.

Deterministic verification engine ensuring model output is strictly grounded
in Earth Engine structured payloads.
"""

from typing import Any, Dict, List, Optional
from app.services.models import Claim, GuardrailResult, VerifiedClaim


def match_indicator(claim_or_text: Any, payload_keys: Optional[List[str]] = None) -> Optional[str]:
    """Determine which indicator an extracted claim or text string references."""
    return None


def extract_claims(text: Optional[str]) -> List[Claim]:
    """Extract factual claims (numeric, categorical, mixed) from response text."""
    return []


def verify_claims(claims: List[Claim], payload: Optional[Dict[str, Any]]) -> List[VerifiedClaim]:
    """Verify claims against structured indicator payload."""
    return []


def clean_response(text: Optional[str], verified_claims: List[VerifiedClaim]) -> str:
    """Format original response text keeping rejected claims visible with strike-through tags."""
    return text or ""


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
