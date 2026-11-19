from fastapi.testclient import TestClient
from app.main import app
from scripts.seed_example import main as seed
from app.config import settings

client = TestClient(app)


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
    assert client.get("/api/v1/health").json()["status"] == "ok"


def test_departments_after_seed():
    seed()
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/departments", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 11

    response = client.get("/api/v1/departments/D99", headers=headers)
    assert response.status_code == 404
