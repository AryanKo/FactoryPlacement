import asyncio
from pathlib import Path

import ee

from app.core.config import BACKEND_DIR, PROJECT_ROOT, settings
from app.core.logging import logger
from app.models.risk import IndicatorValue, RiskIndicators


class GEEClient:
    _initialized = False

    def __init__(self) -> None:
        self.use_mock = settings.use_mock_gee
        if not self.use_mock and not GEEClient._initialized:
            try:
                credentials = self._build_credentials()
                if credentials is None:
                    logger.error(
                        "GEE credentials missing. Set GEE_SERVICE_ACCOUNT_KEY_PATH, "
                        "GEE_SERVICE_ACCOUNT_JSON, GOOGLE_APPLICATION_CREDENTIALS, "
                        "or EE_PRIVATE_KEY with GEE_SERVICE_ACCOUNT_EMAIL."
                    )
                    return

                initialize_kwargs = {}
                if settings.gee_project_id:
                    initialize_kwargs["project"] = settings.gee_project_id

                ee.Initialize(credentials, **initialize_kwargs)
                GEEClient._initialized = True
                logger.info("Successfully initialized real GEE client")
            except Exception as e:
                logger.error(f"Failed to initialize GEE client: {e!s}")

    def _build_credentials(self):
        """Build Earth Engine service account credentials from configured sources."""
        service_account = settings.ee_service_account or None

        key_json = settings.gee_service_account_json.strip()
        if key_json:
            return ee.ServiceAccountCredentials(
                service_account,
                key_data=key_json.replace("\\n", "\n"),
            )

        key_ref = (
            settings.ee_private_key or settings.google_application_credentials
        ).strip()
        if not key_ref:
            return None

        key_path = self._resolve_key_path(key_ref)
        if key_path:
            return ee.ServiceAccountCredentials(service_account, key_file=str(key_path))

        if self._looks_like_key_path(key_ref):
            logger.error(f"GEE service account key file not found: {key_ref}")
            return None

        if not service_account:
            logger.error("Raw EE_PRIVATE_KEY requires GEE_SERVICE_ACCOUNT_EMAIL.")
            return None

        return ee.ServiceAccountCredentials(
            service_account,
            key_data=key_ref.replace("\\n", "\n"),
        )

    def _resolve_key_path(self, value: str) -> Path | None:
        """Resolve absolute or project-relative service account key paths."""
        candidate = Path(value).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate

        for base_dir in (Path.cwd(), BACKEND_DIR, PROJECT_ROOT):
            path = (base_dir / candidate).resolve()
            if path.exists():
                return path

        return None

    def _looks_like_key_path(self, value: str) -> bool:
        """Return true when a configured key value is intended as a file path."""
        return value.lower().endswith(".json") or "\\" in value or "/" in value

    def _sync_get_all_indicators(
        self, lat: float, lon: float
    ) -> tuple[float | None, str | None]:
        """Blocking call to GEE fetching both surface water trend and flood exposure in one request."""
        point = ee.Geometry.Point([lon, lat])

        # JRC Global Surface Water dataset (v1.4)
        dataset = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")

        # Select both bands to combine into a single API call
        combined = dataset.select(["change_norm", "max_extent"])

        result = combined.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=30,
            maxPixels=1e4,
        ).getInfo()

        if not result:
            return None, None

        change_val = result.get("change_norm")
        extent_val = result.get("max_extent")

        trend = float(change_val) if change_val is not None else None

        flood = None
        if extent_val is not None:
            extent_float = float(extent_val)
            if extent_float > 0.5:
                flood = "high"
            elif extent_float > 0:
                flood = "moderate"
            else:
                flood = "low"

        return trend, flood

    async def _async_get_indicators(
        self, lat: float, lon: float, timeout: float = 8.0
    ) -> tuple[float | None, str | None]:
        """Runs the synchronous GEE function in a thread with a timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_get_all_indicators, lat, lon),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"GEE query timed out after {timeout} seconds.")
            return None, None
        except Exception as e:
            logger.error(f"GEE query failed: {e!s}")
            return None, None

    async def get_risk_indicators(self, lat: float, lon: float) -> RiskIndicators:
        """Return risk indicators for the given coordinates."""
        if self.use_mock:
            logger.info(f"Returning MOCK risk indicators for lat={lat}, lon={lon}")
            return RiskIndicators(
                surface_water_trend=IndicatorValue(
                    value=None,
                    source="MOCK_GEE/JRC-GSW",
                    confidence="no_data",
                ),
                flood_exposure=IndicatorValue(
                    value=None,
                    source="MOCK_GEE/flood-layer",
                    confidence="no_data",
                ),
                rainfall_proxy=IndicatorValue(
                    value=None,
                    source=None,
                    confidence="no_data",
                ),
            )

        if not GEEClient._initialized:
            logger.error("GEE is not initialized. Falling back to no_data.")
            return self._get_fallback_indicators()

        logger.info(f"Fetching real GEE data for lat={lat}, lon={lon}")

        # Fetch both indicators in a single GEE HTTP request
        trend_val, flood_val = await self._async_get_indicators(lat, lon)

        if trend_val is not None:
            trend_indicator = IndicatorValue(
                value=trend_val,
                unit="% change 10yr",
                source="GEE/JRC-GSW",
                confidence="measured",
            )
        else:
            trend_indicator = IndicatorValue(value=None, confidence="no_data")

        if flood_val is not None:
            flood_indicator = IndicatorValue(
                value=flood_val,
                source="GEE/flood-layer",
                confidence="measured",
            )
        else:
            flood_indicator = IndicatorValue(value=None, confidence="no_data")

        return RiskIndicators(
            surface_water_trend=trend_indicator,
            flood_exposure=flood_indicator,
            rainfall_proxy=IndicatorValue(
                value=None, source=None, confidence="no_data"
            ),
        )

    def _get_fallback_indicators(self) -> RiskIndicators:
        """Return all-no_data indicators for any unrecoverable failure."""
        return RiskIndicators(
            surface_water_trend=IndicatorValue(value=None, confidence="no_data"),
            flood_exposure=IndicatorValue(value=None, confidence="no_data"),
            rainfall_proxy=IndicatorValue(value=None, confidence="no_data"),
        )


def get_gee_client() -> GEEClient:
    """FastAPI dependency provider."""
    return GEEClient()
