import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from scripts.seed_example import main as seed


client = TestClient(app)

DATASET_AVAILABLE = (
    Path(settings.data_dir) / "departments.csv"
).is_file()


def get_admin_token():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "sanjay.kumar@znova-demo.example",
            "password": settings.demo_admin_password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.skipif(
    not DATASET_AVAILABLE,
    reason="Company CSV dataset is not available in CI",
)
def test_departments_after_seed():
    seed()

    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/departments", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 11

    response = client.get("/api/v1/departments/D99", headers=headers)
    assert response.status_code == 404