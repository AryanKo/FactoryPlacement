import asyncio
from pathlib import Path

import ee

from app.core.config import BACKEND_DIR, PROJECT_ROOT, settings
from app.core.logging import logger
from app.models.risk import IndicatorValue, RiskIndicators


class GEEClient:
    _initialized = False
    LAND_COVER_CLASSES = {
        1: "Evergreen Needleleaf Forests",
        2: "Evergreen Broadleaf Forests",
        3: "Deciduous Needleleaf Forests",
        4: "Deciduous Broadleaf Forests",
        5: "Mixed Forests",
        6: "Closed Shrublands",
        7: "Open Shrublands",
        8: "Woody Savannas",
        9: "Savannas",
        10: "Grasslands",
        11: "Permanent Wetlands",
        12: "Croplands",
        13: "Urban and Built-up Lands",
        14: "Cropland/Natural Vegetation Mosaics",
        15: "Permanent Snow and Ice",
        16: "Barren",
        17: "Water Bodies",
    }

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
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to initialize GEE client: {e!s}")

    def _build_credentials(self):  # noqa: ANN202
        """Build Earth Engine service account credentials from configured sources."""
        service_account = settings.ee_service_account or None

        key_json = settings.gee_service_account_json.strip()
        if key_json:
            return ee.ServiceAccountCredentials(
                service_account,
                key_data=key_json.replace("\\n", "\n"),
            )

        key_ref = (settings.ee_private_key or settings.google_application_credentials).strip()
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

    # (legacy implementation removed) - comprehensive implementation below
        # New implementation starts here
    def _sync_get_all_indicators(
        self, lat: float, lon: float
    ) -> tuple[
        float | None,
        str | None,
        float | None,
        float | None,
        float | None,
        str | None,
        float | None,
        float | None,
        float | None,
    ]:
        """Blocking call to GEE fetching multiple indicators in one request.

        Returns a tuple in the order:
        (surface_water_trend, flood_exposure, rainfall, elevation, slope,
         land_cover, vegetation_index, surface_temperature, distance_to_water)

        Each value is either a measured value or None.
        """
        point = ee.Geometry.Point([lon, lat])

        # Build images (without per-band reduceRegion) and perform a single combined query.
        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(days=365)

        # Water bands (prefer change_norm when available)
        water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
        water_bands = water.select(["change_norm", "max_extent"])

        # Rainfall: CHIRPS daily precipitation summed over the past year -> mm/year
        chirps_sum = (
            ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            .select("precipitation")
            .sum()
            .rename("rainfall")
        )

        # Elevation and slope (SRTM preferred)
        elev_img = ee.Image("USGS/SRTMGL1_003").select("elevation")
        slope_img = ee.Terrain.slope(elev_img).rename("slope")

        # Land cover (MODIS IGBP, LC_Type1)
        lc_img = (
            ee.ImageCollection("MODIS/061/MCD12Q1").first().select("LC_Type1").rename("land_cover")
        )

        # Vegetation index (MODIS NDVI, scaled)
        ndvi_img = (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .select("NDVI")
            .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            .mean()
            .multiply(0.0001)
            .rename("vegetation_index")
        )

        # Surface temperature (MODIS LST)
        lst_img = (
            ee.ImageCollection("MODIS/061/MOD11A2")
            .select("LST_Day_1km")
            .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            .mean()
            .rename("surface_temperature")
        )

        # Distance to water (derived from max_extent)
        water_mask = water.select("max_extent").gt(0).selfMask()
        distance_img = water_mask.distance(ee.Kernel.euclidean(50000, "meters"), False).rename("distance_to_water")

        combined = water_bands.addBands([
            chirps_sum,
            elev_img,
            slope_img,
            lc_img,
            ndvi_img,
            lst_img,
            distance_img,
        ])

        result = combined.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=500,
            maxPixels=1e6,
        ).getInfo()

        # extract and normalise values
        change_val = None
        if result:
            change_val = result.get("change_norm") if result.get("change_norm") is not None else result.get("change")
        extent_val = result.get("max_extent") if result else None

        trend = float(change_val) if change_val is not None else None
        # Keep raw max_extent numeric value here; classification to 'high/moderate/low'
        # is performed later by _flood_indicator so that the low-level query returns
        # measured numeric values or None.
        max_extent_raw = float(extent_val) if extent_val is not None else None

        # rainfall is the summed precipitation over the period (mm/year)
        rainfall = float(result.get("rainfall")) if result and result.get("rainfall") is not None else None
        elevation = float(result.get("elevation")) if result and result.get("elevation") is not None else None
        slope = float(result.get("slope")) if result and result.get("slope") is not None else None
        lc_code = int(result.get("land_cover")) if result and result.get("land_cover") is not None else None
        vegetation_index = float(result.get("vegetation_index")) if result and result.get("vegetation_index") is not None else None
        surface_temperature = float(result.get("surface_temperature")) * 0.02 - 273.15 if result and result.get("surface_temperature") is not None else None
        distance_to_water = float(result.get("distance_to_water")) if result and result.get("distance_to_water") is not None else None

        return {
            "change_norm": trend,
            "max_extent": max_extent_raw,
            "rainfall": rainfall,
            "elevation": elevation,
            "slope": slope,
            "land_cover": lc_code if lc_code is not None else None,
            "vegetation_index": vegetation_index,
            "surface_temperature": surface_temperature,
            "distance_to_water": distance_to_water,
        }

    async def _async_get_indicators(
        self, lat: float, lon: float, timeout: float = 8.0
    ) -> dict[str, float | None]:
        """Runs the synchronous GEE function in a thread with a timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_get_all_indicators, lat, lon),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"GEE query timed out after {timeout} seconds.")
            return {}
        except Exception as e:  # noqa: BLE001
            logger.error(f"GEE query failed: {e!s}")
            return {}

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
                rainfall=IndicatorValue(value=None, source="MOCK_GEE/ERA5-Land", confidence="no_data"),
                elevation=IndicatorValue(value=None, source="MOCK_GEE/ETOPO1", confidence="no_data"),
                slope=IndicatorValue(value=None, source="MOCK_GEE/ETOPO1", confidence="no_data"),
                land_cover=IndicatorValue(value=None, source="MOCK_GEE/MODIS-MCD12Q1", confidence="no_data"),
                vegetation_index=IndicatorValue(value=None, source="MOCK_GEE/MODIS-MOD13Q1", confidence="no_data"),
                surface_temperature=IndicatorValue(value=None, source="MOCK_GEE/MODIS-MOD11A2", confidence="no_data"),
                distance_to_water=IndicatorValue(value=None, source="MOCK_GEE/JRC-GSW", confidence="no_data"),
            )

        if not GEEClient._initialized:
            logger.error("GEE is not initialized. Falling back to no_data.")
            return self._get_fallback_indicators()

        logger.info(f"Fetching real GEE data for lat={lat}, lon={lon}")

        raw_values = await self._async_get_indicators(lat, lon)
        indicators = RiskIndicators(
            surface_water_trend=self._numeric_indicator(
                raw_values.get("change_norm"),
                unit="% normalized change",
                source="GEE/JRC-GSW",
            ),
            flood_exposure=self._flood_indicator(raw_values.get("max_extent")),
            rainfall=self._numeric_indicator(
                raw_values.get("rainfall"),
                unit="mm/year",
                source="GEE/CHIRPS",
                minimum=0,
            ),
            elevation=self._numeric_indicator(
                raw_values.get("elevation"),
                unit="m",
                source="GEE/NOAA-ETOPO1",
            ),
            slope=self._numeric_indicator(
                raw_values.get("slope"),
                unit="degrees",
                source="GEE/NOAA-ETOPO1",
                minimum=0,
            ),
            land_cover=self._land_cover_indicator(raw_values.get("land_cover")),
            vegetation_index=self._numeric_indicator(
                raw_values.get("vegetation_index"),
                unit="NDVI",
                source="GEE/MODIS-MOD13Q1",
                minimum=-1,
                maximum=1,
            ),
            surface_temperature=self._numeric_indicator(
                raw_values.get("surface_temperature"),
                unit="Celsius",
                source="GEE/MODIS-MOD11A2",
            ),
            distance_to_water=self._numeric_indicator(
                raw_values.get("distance_to_water"),
                unit="m",
                source="GEE/JRC-GSW",
                minimum=0,
            ),
            rainfall_proxy=IndicatorValue(value=None, source=None, confidence="no_data"),

        )

        # Deprecation signal: once `rainfall` is implemented and measured, the
        # legacy `rainfall_proxy` field is redundant. Keep the field for
        # backward compatibility but log a warning for downstream consumers.
        try:
            if indicators.rainfall and indicators.rainfall.confidence == "measured":
                logger.warning("'rainfall_proxy' is deprecated; use 'rainfall' (mm/year) instead.")
        except Exception:
            # be resilient against Pydantic access oddities in tests
            pass

        return indicators

    def _numeric_indicator(
        self,
        value: float | int | None,
        unit: str,
        source: str,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> IndicatorValue:
        """Map a raw numeric GEE value to a measured/no_data indicator."""
        if value is None:
            return IndicatorValue(value=None, confidence="no_data")

        numeric_value = float(value)
        if minimum is not None and numeric_value < minimum:
            return IndicatorValue(value=None, confidence="no_data")
        if maximum is not None and numeric_value > maximum:
            return IndicatorValue(value=None, confidence="no_data")

        return IndicatorValue(
            value=round(numeric_value, 4),
            unit=unit,
            source=source,
            confidence="measured",
        )

    def _flood_indicator(self, value: float | int | None) -> IndicatorValue:
        """Convert JRC max_extent water presence to a simple exposure class."""
        if value is None:
            return IndicatorValue(value=None, confidence="no_data")

        extent_float = float(value)
        if extent_float > 0.5:
            flood = "high"
        elif extent_float > 0:
            flood = "moderate"
        else:
            flood = "low"

        return IndicatorValue(
            value=flood,
            source="GEE/JRC-GSW",
            confidence="measured",
        )

    def _land_cover_indicator(self, value: float | int | None) -> IndicatorValue:
        """Convert MODIS IGBP class code to a named land-cover class."""
        if value is None:
            return IndicatorValue(value=None, confidence="no_data")

        class_id = int(value)
        class_name = self.LAND_COVER_CLASSES.get(class_id)
        if class_name is None:
            return IndicatorValue(value=None, confidence="no_data")

        return IndicatorValue(
            value=f"{class_name} ({class_id})",
            unit="IGBP class",
            source="GEE/MODIS-MCD12Q1",
            confidence="measured",
        )

    def _get_fallback_indicators(self) -> RiskIndicators:
        """Return all-no_data indicators for any unrecoverable failure."""
        return RiskIndicators(
            surface_water_trend=IndicatorValue(value=None, confidence="no_data"),
            flood_exposure=IndicatorValue(value=None, confidence="no_data"),
            rainfall=IndicatorValue(value=None, confidence="no_data"),
            elevation=IndicatorValue(value=None, confidence="no_data"),
            slope=IndicatorValue(value=None, confidence="no_data"),
            land_cover=IndicatorValue(value=None, confidence="no_data"),
            vegetation_index=IndicatorValue(value=None, confidence="no_data"),
            distance_to_water=IndicatorValue(value=None, confidence="no_data"),
            rainfall_proxy=IndicatorValue(value=None, confidence="no_data"),
        )


def get_gee_client() -> GEEClient:
    """FastAPI dependency provider."""
    return GEEClient()
