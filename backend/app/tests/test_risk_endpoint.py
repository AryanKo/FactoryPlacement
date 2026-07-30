from datetime import datetime
from unittest.mock import patch

import pytest
from app.core.config import Settings, settings
from app.main import app
from app.services.gee_client import GEEClient
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_gee_settings():
    original_values = {
        "use_mock_gee": settings.use_mock_gee,
        "ee_service_account": settings.ee_service_account,
        "ee_private_key": settings.ee_private_key,
        "gee_service_account_json": settings.gee_service_account_json,
        "google_application_credentials": settings.google_application_credentials,
        "gee_project_id": settings.gee_project_id,
    }
    original_initialized = GEEClient._initialized

    yield

    for key, value in original_values.items():
        setattr(settings, key, value)
    GEEClient._initialized = original_initialized


def test_get_risk_valid():
    settings.use_mock_gee = True
    response = client.get("/api/risk?lat=37.7749&lon=-122.4194")
    assert response.status_code == 200
    data = response.json()

    assert "location" in data
    assert data["location"]["lat"] == 37.7749
    assert data["location"]["lon"] == -122.4194

    assert "indicators" in data
    assert "surface_water_trend" in data["indicators"]
    assert "flood_exposure" in data["indicators"]
    assert "rainfall_proxy" in data["indicators"]

    # Check no_data adherence
    assert data["indicators"]["rainfall_proxy"]["value"] is None
    assert data["indicators"]["rainfall_proxy"]["confidence"] == "no_data"
    assert "computed_at" in data
    assert datetime.fromisoformat(data["computed_at"].replace("Z", "+00:00"))


def test_get_risk_coordinates_echo():
    settings.use_mock_gee = True

    response1 = client.get("/api/risk?lat=37.7749&lon=-122.4194")
    response2 = client.get("/api/risk?lat=40.7128&lon=-74.0060")

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    assert data1["location"]["lat"] == 37.7749
    assert data1["location"]["lon"] == -122.4194
    assert data2["location"]["lat"] == 40.7128
    assert data2["location"]["lon"] == -74.0060
    assert data1["location"] != data2["location"]
    assert datetime.fromisoformat(data1["computed_at"].replace("Z", "+00:00"))
    assert datetime.fromisoformat(data2["computed_at"].replace("Z", "+00:00"))


def test_get_risk_invalid_params():
    response = client.get("/api/risk?lat=abc")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"] == "Validation Error"


@patch.object(GEEClient, "_sync_get_all_indicators")
def test_gee_production_success(mock_sync):
    # Setup mock GEE response
    mock_sync.return_value = (5.5, "high")

    # Temporarily force production mode
    settings.use_mock_gee = False
    # Mock GEE initialization to bypass credential check
    GEEClient._initialized = True

    response = client.get("/api/risk?lat=37.7749&lon=-122.4194")
    assert response.status_code == 200
    data = response.json()

    assert data["indicators"]["surface_water_trend"]["value"] == 5.5
    assert data["indicators"]["surface_water_trend"]["confidence"] == "measured"
    assert data["indicators"]["flood_exposure"]["value"] == "high"
    assert data["indicators"]["flood_exposure"]["confidence"] == "measured"

    # Restore settings
    settings.use_mock_gee = True


@patch.object(GEEClient, "_sync_get_all_indicators")
def test_gee_production_exception_fallback(mock_sync):
    # Simulate GEE quota error or geometry error
    mock_sync.side_effect = Exception("Earth Engine capacity exceeded")

    settings.use_mock_gee = False
    GEEClient._initialized = True

    response = client.get("/api/risk?lat=37.7749&lon=-122.4194")
    assert response.status_code == 200
    data = response.json()

    # Must fallback to no_data without crashing
    assert data["indicators"]["surface_water_trend"]["value"] is None
    assert data["indicators"]["surface_water_trend"]["confidence"] == "no_data"
    assert data["indicators"]["flood_exposure"]["value"] is None
    assert data["indicators"]["flood_exposure"]["confidence"] == "no_data"

    # Restore settings
    settings.use_mock_gee = True


def test_settings_load_documented_gee_env_names(monkeypatch):
    monkeypatch.setenv("USE_MOCK_GEE", "true")
    monkeypatch.setenv(
        "GEE_SERVICE_ACCOUNT_EMAIL", "svc@example.iam.gserviceaccount.com"
    )
    monkeypatch.setenv("GEE_SERVICE_ACCOUNT_KEY_PATH", "service-account.json")
    monkeypatch.setenv("GEE_PROJECT_ID", "aquashield-demo")

    loaded = Settings()

    assert loaded.use_mock_gee is True
    assert loaded.ee_service_account == "svc@example.iam.gserviceaccount.com"
    assert loaded.ee_private_key == "service-account.json"
    assert loaded.gee_project_id == "aquashield-demo"


@patch("app.services.gee_client.ee.Initialize")
@patch("app.services.gee_client.ee.ServiceAccountCredentials")
def test_gee_initializes_with_documented_key_path(
    mock_credentials, mock_initialize, tmp_path
):
    key_file = tmp_path / "service-account.json"
    key_file.write_text(
        '{"type":"service_account","client_email":"svc@example.iam.gserviceaccount.com"}',
        encoding="utf-8",
    )
    credentials = object()
    mock_credentials.return_value = credentials

    settings.use_mock_gee = False
    settings.ee_service_account = "svc@example.iam.gserviceaccount.com"
    settings.ee_private_key = str(key_file)
    settings.gee_service_account_json = ""
    settings.google_application_credentials = ""
    settings.gee_project_id = "aquashield-demo"
    GEEClient._initialized = False

    GEEClient()

    mock_credentials.assert_called_once_with(
        "svc@example.iam.gserviceaccount.com",
        key_file=str(key_file),
    )
    mock_initialize.assert_called_once_with(credentials, project="aquashield-demo")
    assert GEEClient._initialized is True


@patch("app.services.gee_client.ee.Initialize")
@patch("app.services.gee_client.ee.ServiceAccountCredentials")
def test_gee_missing_key_path_does_not_initialize(
    mock_credentials, mock_initialize, tmp_path
):
    settings.use_mock_gee = False
    settings.ee_service_account = "svc@example.iam.gserviceaccount.com"
    settings.ee_private_key = str(tmp_path / "missing-service-account.json")
    settings.gee_service_account_json = ""
    settings.google_application_credentials = ""
    settings.gee_project_id = "aquashield-demo"
    GEEClient._initialized = False

    GEEClient()

    mock_credentials.assert_not_called()
    mock_initialize.assert_not_called()
    assert GEEClient._initialized is False


@patch("app.services.gee_client.ee")
def test_gee_query_uses_lon_lat_geometry(mock_ee):
    mock_ee.Image.return_value.select.return_value.reduceRegion.return_value.getInfo.return_value = {
        "change_norm": 1.25,
        "max_extent": 1,
    }

    client_instance = object.__new__(GEEClient)
    trend, flood = client_instance._sync_get_all_indicators(12.3, 45.6)

    mock_ee.Geometry.Point.assert_called_once_with([45.6, 12.3])
    assert trend == 1.25
    assert flood == "high"


def test_gee_auth_failure_fallback():
    settings.use_mock_gee = False
    # Simulate uninitialized client (e.g. auth failed during startup)
    GEEClient._initialized = False

    response = client.get("/api/risk?lat=37.7749&lon=-122.4194")
    assert response.status_code == 200
    data = response.json()

    assert data["indicators"]["surface_water_trend"]["value"] is None
    assert data["indicators"]["surface_water_trend"]["confidence"] == "no_data"

    # Restore settings
    settings.use_mock_gee = True
