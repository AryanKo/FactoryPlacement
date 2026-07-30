"""Data models for Guardrail Core service."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimType(str, Enum):
    """Enumeration of claim types for verification."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class Claim:
    """Represents a factual claim extracted from text."""

    text: str
    original_sentence: str
    claim_type: ClaimType
    indicator_alias: str | None = None
    extracted_number: float | None = None
    extracted_category: str | None = None


@dataclass
class VerifiedClaim:
    """Represents the verification result for a single claim."""

    claim: Claim
    verified: bool
    reason: str
    matched_indicator: str | None = None
    payload_value: Any = None


@dataclass
class GuardrailResult:
    """Result returned by the guardrail master verify API."""

    clean_text: str
    claims_checked: int
    claims_grounded: int
    claims_rejected: int
    trust_score: float
    rejected_claims: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert GuardrailResult to a standard dictionary representation."""
        return {
            "clean_text": self.clean_text,
            "claims_checked": self.claims_checked,
            "claims_grounded": self.claims_grounded,
            "claims_rejected": self.claims_rejected,
            "trust_score": self.trust_score,
            "rejected_claims": self.rejected_claims,
        }
