import asyncio
from app.services.gee_client import GEEClient

# Sample realistic stubbed raw GEE outputs for three locations
SAMPLES = {
    # Chennai (approx): high annual rainfall ~1300 mm/year
    (13.0827, 80.2707): {
        "change_norm": -38.0,
        "max_extent": 0.0,
        "rainfall": 1300.0,
        "elevation": 8.0,
        "slope": 0.18,
        "land_cover": 13,
        "vegetation_index": 0.31,
        "surface_temperature": 303.15,  # stored as MODIS LST raw units (will be scaled in code)
        "distance_to_water": 707.0,
    },
    # Sahara sample: very low rainfall
    (23.4162, 25.6628): {
        "change_norm": 0.0,
        "max_extent": 0.0,
        "rainfall": 25.0,
        "elevation": 200.0,
        "slope": 1.5,
        "land_cover": 16,
        "vegetation_index": 0.02,
        "surface_temperature": 315.15,
        "distance_to_water": 5000.0,
    },
    # Amazon sample: very high rainfall and NDVI
    (-3.20, -60.00): {
        "change_norm": -5.0,
        "max_extent": 0.2,
        "rainfall": 2500.0,
        "elevation": 50.0,
        "slope": 2.0,
        "land_cover": 2,
        "vegetation_index": 0.82,
        "surface_temperature": 299.15,
        "distance_to_water": 200.0,
    },
}


class StubGEEClient(GEEClient):
    async def _async_get_indicators(self, lat: float, lon: float, timeout: float = 8.0):
        # return the closest sample by coordinate
        key = None
        for k in SAMPLES:
            if abs(k[0] - lat) < 0.5 and abs(k[1] - lon) < 0.5:
                key = k
                break
        if key is None:
            # default fallback: return a moderate urban value
            return SAMPLES[(13.0827, 80.2707)]
        return SAMPLES[key]


async def run():
    # Try to initialize a real GEE client if credentials are available and
    # `use_mock_gee` is not set. Otherwise fall back to the stubbed samples.
    from app.core.config import settings

    real_client = GEEClient()
    if not settings.use_mock_gee and GEEClient._initialized:
        client = real_client
        print("Using real GEE client")
    else:
        client = StubGEEClient()
        print("Using stubbed GEE samples")
    locations = [
        (13.0827, 80.2707, "Chennai"),
        (23.4162, 25.6628, "Sahara sample"),
        (-3.20, -60.00, "Amazon sample"),
    ]

    for lat, lon, name in locations:
        indicators = await client.get_risk_indicators(lat, lon)
        print("---", name)
        print(indicators.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(run())
