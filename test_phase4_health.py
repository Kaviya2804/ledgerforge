from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

with patch("app.main.engine.connect", side_effect=Exception("Database unavailable")):
    response = client.get("/api/v1/health")

print("HTTP Status:", response.status_code)
print("Response:", response.json())

assert response.status_code == 503
print("Phase 4 failure test PASSED")
