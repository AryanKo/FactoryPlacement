from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

    model_config = ConfigDict(extra="forbid")


class IndicatorValue(BaseModel):
    value: float | str | None = None
    unit: str | None = None
    source: str | None = None
    confidence: Literal["measured", "no_data"]

class RiskIndicators(BaseModel):
    surface_water_trend: IndicatorValue
    flood_exposure: IndicatorValue
    rainfall: IndicatorValue
    elevation: IndicatorValue
    slope: IndicatorValue
    land_cover: IndicatorValue
    vegetation_index: IndicatorValue
    surface_temperature: IndicatorValue
    distance_to_water: IndicatorValue
    rainfall_proxy: IndicatorValue

    model_config = ConfigDict(extra="forbid")

class RiskRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

    model_config = ConfigDict(extra="forbid")

class RiskResponse(BaseModel):
    location: Location
    indicators: RiskIndicators
    computed_at: datetime

    model_config = ConfigDict(extra="forbid")
