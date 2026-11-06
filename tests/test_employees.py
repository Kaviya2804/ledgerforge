import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date

from app.main import app
from app.database import Base, get_db
from app.models import Employee, User
from app.auth_service import hash_password


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create an ADMIN employee and user in the test database.
    with TestingSessionLocal() as db:
        admin_employee = Employee(
            emp_id="ADMIN001",
            full_name="Test Admin",
            work_email="admin.test@example.com",
            hire_date=date(2020, 1, 1),
            employment_status="Active",
            employment_type="Permanent",
        )
        db.add(admin_employee)
        db.flush()

        admin_user = User(
            user_id="TEST-ADMIN",
            employee_id="ADMIN001",
            username="test.admin@example.com",
            password_hash=hash_password("TestAdmin@123"),
            role="ADMIN",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()

    with TestClient(app) as test_client:
        login_response = test_client.post(
            "/auth/login",
            json={
                "username": "test.admin@example.com",
                "password": "TestAdmin@123",
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        test_client.headers.update({
            "Authorization": f"Bearer {token}"
        })

        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_list_employees(client):
    response = client.get("/employees/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_employees(client):
    response = client.get("/employees/?search=Jatin")
    assert response.status_code == 200


def test_filter_by_department(client):
    response = client.get("/employees/?department_id=D08")
    assert response.status_code == 200


def test_get_missing_employee(client):
    response = client.get("/employees/EMP-99999")
    assert response.status_code == 404


def test_invalid_pagination(client):
    response = client.get("/employees/?page=0")
    assert response.status_code == 422


def test_invalid_page_size(client):
    response = client.get("/employees/?page_size=101")
    assert response.status_code == 422


def test_create_employee(client):
    employee_data = {
        "emp_id": "EMP101",
        "full_name": "Test Employee",
        "work_email": "test.employee@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    response = client.post("/employees/", json=employee_data)

    assert response.status_code == 201
    assert response.json()["emp_id"] == "EMP101"


def test_update_employee(client):
    employee_data = {
        "emp_id": "EMP102",
        "full_name": "Test Employee",
        "work_email": "test102@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    create_response = client.post("/employees/", json=employee_data)
    assert create_response.status_code == 201

    update_data = {"work_location": "Chennai"}
    response = client.patch("/employees/EMP102", json=update_data)

    assert response.status_code == 200
    assert response.json()["work_location"] == "Chennai"


def test_delete_employee(client):
    employee_data = {
        "emp_id": "EMP103",
        "full_name": "Delete Test Employee",
        "work_email": "delete.test@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    create_response = client.post("/employees/", json=employee_data)
    assert create_response.status_code == 201

    response = client.delete("/employees/EMP103")
    assert response.status_code == 204

    get_response = client.get("/employees/EMP103")
    assert get_response.status_code == 200


def test_team_endpoint(client):
    employee_data = {
        "emp_id": "EMP104",
        "full_name": "Team Test Employee",
        "work_email": "team.test@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    create_response = client.post("/employees/", json=employee_data)
    assert create_response.status_code == 201

    response = client.get("/employees/EMP104/team")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_existing_employee(client):
    employee_data = {
        "emp_id": "EMP105",
        "full_name": "Get Test Employee",
        "work_email": "get.test@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    create_response = client.post("/employees/", json=employee_data)
    assert create_response.status_code == 201

    response = client.get("/employees/EMP105")

    assert response.status_code == 200
    assert response.json()["emp_id"] == "EMP105"
    assert response.json()["full_name"] == "Get Test Employee"


def test_employee_response_excludes_dob(client):
    employee_data = {
        "emp_id": "EMP106",
        "full_name": "Privacy Test Employee",
        "work_email": "privacy.test@example.com",
        "hire_date": "2025-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    create_response = client.post("/employees/", json=employee_data)
    assert create_response.status_code == 201

    response = client.get("/employees/EMP106")

    assert response.status_code == 200
    assert "dob" not in response.json()
    assert "date_of_birth" not in response.json()


def test_team_excludes_former_employees_by_default(client):
    manager_data = {
        "emp_id": "MGR107",
        "full_name": "Test Manager",
        "work_email": "manager.test@example.com",
        "hire_date": "2020-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    employee_data = {
        "emp_id": "EMP107",
        "full_name": "Former Team Member",
        "work_email": "former.member@example.com",
        "hire_date": "2021-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
        "manager_id": "MGR107",
    }

    assert client.post("/employees/", json=manager_data).status_code == 201
    assert client.post("/employees/", json=employee_data).status_code == 201
    assert client.delete("/employees/EMP107").status_code == 204

    response = client.get("/employees/MGR107/team")

    assert response.status_code == 200
    assert all(
        employee["emp_id"] != "EMP107"
        for employee in response.json()
    )


def test_team_includes_former_employees_when_requested(client):
    manager_data = {
        "emp_id": "MGR108",
        "full_name": "Test Manager",
        "work_email": "manager108@example.com",
        "hire_date": "2020-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
    }

    employee_data = {
        "emp_id": "EMP108",
        "full_name": "Former Team Member",
        "work_email": "former108@example.com",
        "hire_date": "2021-01-01",
        "employment_status": "Active",
        "employment_type": "Permanent",
        "manager_id": "MGR108",
    }

    assert client.post("/employees/", json=manager_data).status_code == 201
    assert client.post("/employees/", json=employee_data).status_code == 201
    assert client.delete("/employees/EMP108").status_code == 204

    response = client.get(
        "/employees/MGR108/team?include_former=true"
    )

    assert response.status_code == 200
    assert any(
        employee["emp_id"] == "EMP108"
        for employee in response.json()
    )