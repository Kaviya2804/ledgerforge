from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Department,
    Employee,
    Holiday,
    LeaveBalance,
    LeaveType,
)
from app.leave_service import (
    apply_leave,
    approve_leave,
    calculate_leave_days,
    get_leave_balance,
    reject_leave,
    validate_leave_application,
)


@pytest.fixture
def session():
    """Create an isolated temporary database for testing."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    department = Department(
        department_id="D001",
        department_name="Testing",
        cost_center="CC001",
        description="Test department",
    )
    db.add(department)

    employee = Employee(
        emp_id="EMP-TEST-001",
        fname="Test",
        lname="Employee",
        full_name="Test Employee",
        work_email="test.employee@example.com",
        hire_date=date(2025, 1, 1),
        employment_status="Active",
        employment_type="Full-time",
        department_id="D001",
    )
    db.add(employee)

    leave_type = LeaveType(
        leave_type_code="CL",
        leave_type_name="Casual Leave",
        pay_type="Paid",
        annual_quota_days=12,
    )
    db.add(leave_type)

    balance = LeaveBalance(
        employee_id="EMP-TEST-001",
        as_of_date=date(2026, 9, 30),
        financial_year="FY2026-27",
        cl_entitlement=12,
        cl_used=2,
        cl_balance=10,
        sl_entitlement=12,
        sl_used=0,
        sl_balance=12,
        el_used_fy=0,
        el_balance=15,
        pending_days=0,
    )
    db.add(balance)

    holiday = Holiday(
        holiday_date=date(2026, 10, 5),
        holiday_name="Test Holiday",
    )
    db.add(holiday)

    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_calculate_leave_days_excludes_weekends_and_holidays(session):
    days = calculate_leave_days(
        session,
        date(2026, 10, 2),
        date(2026, 10, 6),
    )

    assert days == 2


def test_get_leave_balance(session):
    balance = get_leave_balance(
        session,
        "EMP-TEST-001",
        "CL",
    )

    assert balance == 10


def test_validate_leave_application(session):
    result = validate_leave_application(
        session,
        "EMP-TEST-001",
        "CL",
        date(2026, 10, 6),
        date(2026, 10, 7),
    )

    assert result["days"] == 2
    assert result["available_balance"] == 10
    assert result["status"] == "Pending"


def test_reject_leave_when_balance_is_insufficient(session):
    with pytest.raises(ValueError, match="Insufficient CL balance"):
        validate_leave_application(
            session,
            "EMP-TEST-001",
            "CL",
            date(2026, 10, 6),
            date(2026, 10, 30),
        )


def test_reject_end_date_before_start_date(session):
    with pytest.raises(ValueError, match="End date"):
        validate_leave_application(
            session,
            "EMP-TEST-001",
            "CL",
            date(2026, 10, 10),
            date(2026, 10, 6),
        )


def test_apply_leave_creates_pending_request(session):
    request = apply_leave(
        session=session,
        employee_id="EMP-TEST-001",
        leave_type_code="CL",
        start_date=date(2026, 10, 6),
        end_date=date(2026, 10, 7),
        reason="Personal work",
    )

    assert request.leave_request_id == "LR-000001"
    assert request.employee_id == "EMP-TEST-001"
    assert request.leave_type_code == "CL"
    assert request.days == 2
    assert request.status == "Pending"
    assert request.reason == "Personal work"


def test_approve_leave_reduces_balance(session):
    request = apply_leave(
        session=session,
        employee_id="EMP-TEST-001",
        leave_type_code="CL",
        start_date=date(2026, 10, 6),
        end_date=date(2026, 10, 7),
        reason="Personal work",
    )

    approved = approve_leave(
        session=session,
        leave_request_id=request.leave_request_id,
        approver_id="EMP-TEST-001",
    )

    assert approved.status == "Approved"
    assert approved.approver_id == "EMP-TEST-001"
    assert approved.decided_on == date.today()

    assert get_leave_balance(
        session,
        "EMP-TEST-001",
        "CL",
    ) == 8

    balance = (
        session.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == "EMP-TEST-001"
        )
        .first()
    )

    assert balance.cl_used == 4


def test_reject_leave_does_not_reduce_balance(session):
    request = apply_leave(
        session=session,
        employee_id="EMP-TEST-001",
        leave_type_code="CL",
        start_date=date(2026, 10, 6),
        end_date=date(2026, 10, 7),
        reason="Personal work",
    )

    rejected = reject_leave(
        session=session,
        leave_request_id=request.leave_request_id,
        approver_id="EMP-TEST-001",
    )

    assert rejected.status == "Rejected"
    assert rejected.approver_id == "EMP-TEST-001"

    assert get_leave_balance(
        session,
        "EMP-TEST-001",
        "CL",
    ) == 10


def test_cannot_approve_same_request_twice(session):
    request = apply_leave(
        session=session,
        employee_id="EMP-TEST-001",
        leave_type_code="CL",
        start_date=date(2026, 10, 6),
        end_date=date(2026, 10, 7),
        reason="Personal work",
    )

    approve_leave(
        session=session,
        leave_request_id=request.leave_request_id,
        approver_id="EMP-TEST-001",
    )

    with pytest.raises(
        ValueError,
        match="Only pending leave requests",
    ):
        approve_leave(
            session=session,
            leave_request_id=request.leave_request_id,
            approver_id="EMP-TEST-001",
        )

    assert get_leave_balance(
        session,
        "EMP-TEST-001",
        "CL",
    ) == 8