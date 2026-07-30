import sys

from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
passed = True

def run_test(name, condition):
    global passed
    if condition:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}")
        passed = False

print("Running API Validations...")

# Test 4: Swagger
docs = client.get("/docs")
run_test("Test 4 - Swagger", docs.status_code == 200)

# Test 5: OpenAPI
openapi = client.get("/openapi.json")
run_test("Test 5 - OpenAPI", openapi.status_code == 200 and "location" in openapi.text and "indicators" in openapi.text)

# Test 6: Happy Path
res = client.get("/api/risk?lat=13.0827&lon=80.2707")
run_test("Test 6 - Happy Path", res.status_code == 200 and "location" in res.json() and "surface_water_trend" in res.json()["indicators"])

# Test 7: JSON Contract
data = res.json()
confidence_values = [v["confidence"] for k, v in data["indicators"].items()]
run_test("Test 7 - Contract", all(c in ["measured", "no_data"] for c in confidence_values))

# Test 8: Invalid Latitude
res = client.get("/api/risk?lat=500&lon=80")
run_test("Test 8 - Invalid Latitude", res.status_code == 422)

# Test 9: Missing Parameter
res = client.get("/api/risk?lat=12")
run_test("Test 9 - Missing Parameter", res.status_code == 422)

# Test 10: String Input
res = client.get("/api/risk?lat=hello&lon=80")
run_test("Test 10 - String Input", res.status_code == 422)

# Test 11: Mock Mode
settings.use_mock_gee = True
res = client.get("/api/risk?lat=13&lon=80")
run_test("Test 11 - Mock Mode", res.json()["indicators"]["surface_water_trend"]["value"] == -12.4)

# Test 12: Production Mode
settings.use_mock_gee = False
res = client.get("/api/risk?lat=13&lon=80")
run_test("Test 12 - Production Mode", res.json()["indicators"]["surface_water_trend"]["value"] is None and res.json()["indicators"]["surface_water_trend"]["confidence"] == "no_data")

if not passed:
    sys.exit(1)
