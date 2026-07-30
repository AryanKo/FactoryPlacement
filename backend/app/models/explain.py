from pydantic import BaseModel, ConfigDict

from .risk import RiskIndicators


class ExplainRequest(BaseModel):
    indicators: RiskIndicators

    model_config = ConfigDict(extra="forbid")

class Recommendation(BaseModel):
    text: str
    source_doc: str
    source_excerpt: str
    section: str

    model_config = ConfigDict(extra="forbid")

class VerificationStats(BaseModel):
    claims_checked: int
    claims_grounded: int
    claims_rejected: int
    trust_score: float

    model_config = ConfigDict(extra="forbid")

class ExplainResponse(BaseModel):
    explanation: str
    recommendation: Recommendation
    verification: VerificationStats

    model_config = ConfigDict(extra="forbid")
