from dotenv import dotenv_values
from fastapi.testclient import TestClient
from app.main import app

env = dotenv_values(".env")
password = env.get("DEMO_EMPLOYEE_PASSWORD")

if not password:
    print("Employee password not found in .env")
else:
    client = TestClient(app)

    login = client.post(
        "/auth/login",
        json={
            "username": "jatin.jayaraman@znova-demo.example",
            "password": password,
        },
    )

    print("Login status:", login.status_code)

    if login.status_code == 200:
        token = login.json()["access_token"]

        response = client.get(
            "/reports/statutory/2026/4",
            headers={"Authorization": f"Bearer {token}"},
        )

        print("Employee report status:", response.status_code)
        print("Response:", response.text)
