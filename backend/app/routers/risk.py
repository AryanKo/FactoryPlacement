from datetime import datetime, timezone

from app.models.risk import Location, RiskRequest, RiskResponse
from app.services.gee_client import GEEClient, get_gee_client
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("", response_model=RiskResponse)
async def get_risk(
    request: RiskRequest = Depends(), gee_client: GEEClient = Depends(get_gee_client)
):

    indicators = await gee_client.get_risk_indicators(request.lat, request.lon)

    return RiskResponse(
        location=Location(lat=request.lat, lon=request.lon),
        indicators=indicators,
        computed_at=datetime.now(timezone.utc),
    )
