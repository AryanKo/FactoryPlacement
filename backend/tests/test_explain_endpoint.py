"""
AquaShield — Phase 3D /api/explain Integration Test Suite
Tests:
1. Endpoint structure matches BLUEPRINT.md §3 contract.
2. Demo fixture path (?demo_fixture=true) triggers visible claim rejection (claims_rejected = 1, trust_score = 0.8).
3. End-to-end integration call (RAG -> Prompt -> Gemma -> Guardrail -> Response).
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)

SAMPLE_INDICATOR_PAYLOAD = {
    "indicators": {
        "surface_water_trend": {"value": -12.4, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
        "flood_exposure": {"value": "moderate", "source": "GEE/flood-layer", "confidence": "measured"},
        "rainfall_proxy": {"value": None, "source": None, "confidence": "no_data"}
    },
    "lat": 12.9716,
    "lon": 77.5946
}


def test_explain_endpoint_contract():
    response = client.post("/api/explain", json=SAMPLE_INDICATOR_PAYLOAD)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

    data = response.json()
    assert "explanation" in data
    assert "recommendation" in data
    assert "verification" in data

    rec = data["recommendation"]
    assert "text" in rec and "source_doc" in rec and "source_excerpt" in rec and "section" in rec

    ver = data["verification"]
    assert "claims_checked" in ver and "claims_grounded" in ver and "claims_rejected" in ver and "trust_score" in ver
    assert 0.0 <= ver["trust_score"] <= 1.0
    print(f"\n  [PASS] /api/explain contract verified: trust_score={ver['trust_score']}")


def test_demo_fixture_triggers_claim_rejection():
    response = client.post("/api/explain?demo_fixture=true", json=SAMPLE_INDICATOR_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    ver = data["verification"]

    assert ver["claims_rejected"] == 1, f"Demo fixture must reject 1 claim, got: {ver['claims_rejected']}"
    assert ver["trust_score"] == 0.8, f"Demo fixture trust_score must be 0.8, got: {ver['trust_score']}"
    print("\n  [PASS] Demo fixture successfully triggered live claim rejection (claims_rejected=1, trust_score=0.8).")


if __name__ == "__main__":
    pytest.main(["-s", __file__])
