from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from scripts.seed_example import main as seed


client = TestClient(app)


def get_admin_headers():
    seed()

    response = client.post(
        "/auth/login",
        json={
            "username": "sanjay.kumar@znova-demo.example",
            "password": settings.demo_admin_password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_trial_balance_report():
    headers = get_admin_headers()

    response = client.get(
        "/reports/financial/trial-balance",
        params={
            "start_date": "2025-04-01",
            "end_date": "2026-11-03",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["total_debit"]) == Decimal("5298104813.57")
    assert Decimal(data["total_credit"]) == Decimal("5298104813.57")


def test_profit_loss_report():
    headers = get_admin_headers()

    response = client.get(
        "/reports/financial/profit-loss",
        params={
            "start_date": "2025-04-01",
            "end_date": "2026-11-03",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["revenue"]) == Decimal("1260930052.00")
    assert Decimal(data["expenses"]) == Decimal("1036246464.42")
    assert Decimal(data["net_profit"]) == Decimal("224683587.58")


def test_balance_sheet_report():
    headers = get_admin_headers()

    response = client.get(
        "/reports/financial/balance-sheet",
        params={"as_of_date": "2026-11-03"},
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_balanced"] is True
    assert Decimal(data["assets"]) == Decimal("463762958.65")
    assert Decimal(data["liabilities"]) == Decimal("77499607.07")
    assert Decimal(data["equity"]) == Decimal("161579764.00")
    assert Decimal(data["current_profit"]) == Decimal("224683587.58")
    