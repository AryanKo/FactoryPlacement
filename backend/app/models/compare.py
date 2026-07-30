
from pydantic import BaseModel, ConfigDict

from .risk import Location, RiskResponse


class CompareRequest(BaseModel):
    site_a: Location
    site_b: Location

    model_config = ConfigDict(extra="forbid")

class CompareResponse(BaseModel):
    sites: list[RiskResponse]
    diff_summary: str

    model_config = ConfigDict(extra="forbid")
