from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Department,
    Employee,
    Role,
    SalaryComponent,
    SalaryRevision,
    SalaryStructure,
)
from app.salary_service import get_structure, revise_salary


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_get_structure_respects_effective_date(db):
    department = Department(
        department_id="D001",
        department_name="Test Department",
        cost_center="CC001",
        description="Test department",
    )
    db.add(department)

    role = Role(
        role_id="ROLE001",
        department_id="D001",
        role_title="Test Developer",
        level=1,
        grade="G1",
        band_min_annual=Decimal("300000.00"),
        band_mid_annual=Decimal("400000.00"),
        band_max_annual=Decimal("500000.00"),
        overtime_eligible=False,
        band_year=2025,
    )
    db.add(role)

    employee = Employee(
        emp_id="EMP-0001",
        full_name="Test Employee",
        work_email="test.employee@example.com",
        hire_date=date(2024, 1, 1),
        employment_status="Active",
        employment_type="Permanent",
    )
    db.add(employee)

    component = SalaryComponent(
        component_id="BASIC",
        component_name="Basic Salary",
        component_type="EARNING",
        taxable="Y",
        calculation_rule="Fixed",
        is_fixed="Y",
    )
    db.add(component)
    db.flush()

    revision = SalaryRevision(
        revision_id="REV001",
        employee_id="EMP-0001",
        effective_from=date(2026, 1, 1),
        revision_reason="Initial salary",
        previous_annual_fixed=None,
        new_annual_fixed=Decimal("360000.00"),
        pct_change=None,
        role_id_after="ROLE001",
        approved_by=None,
        created_at=datetime.now(),
    )
    db.add(revision)
    db.flush()

    structure = SalaryStructure(
        structure_id="STRUCT001",
        employee_id="EMP-0001",
        component_id="BASIC",
        component_name="Basic Salary",
        component_type="EARNING",
        monthly_amount=Decimal("30000.00"),
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 1, 31),
        revision_id="REV001",
    )
    db.add(structure)
    db.commit()

    before_start = get_structure(
        db,
        "EMP-0001",
        date(2025, 12, 31),
    )

    first_day = get_structure(
        db,
        "EMP-0001",
        date(2026, 1, 1),
    )

    last_day = get_structure(
        db,
        "EMP-0001",
        date(2026, 1, 31),
    )

    after_end = get_structure(
        db,
        "EMP-0001",
        date(2026, 2, 1),
    )

    assert len(before_start) == 0
    assert len(first_day) == 1
    assert len(last_day) == 1
    assert len(after_end) == 0


def test_revise_salary_closes_old_structure(db):
    department = Department(
        department_id="D001",
        department_name="Test Department",
        cost_center="CC001",
        description="Test department",
    )
    db.add(department)

    role = Role(
        role_id="ROLE001",
        department_id="D001",
        role_title="Test Developer",
        level=1,
        grade="G1",
        band_min_annual=Decimal("300000.00"),
        band_mid_annual=Decimal("400000.00"),
        band_max_annual=Decimal("500000.00"),
        overtime_eligible=False,
        band_year=2025,
    )
    db.add(role)

    employee = Employee(
        emp_id="SAL002",
        full_name="Revision Test Employee",
        work_email="revision.test@example.com",
        hire_date=date(2024, 1, 1),
        employment_status="Active",
        employment_type="Permanent",
    )
    db.add(employee)

    components = [
        SalaryComponent(
            component_id="BASIC",
            component_name="Basic Salary",
            component_type="EARNING",
            taxable="Y",
            calculation_rule="40% of monthly fixed gross",
            is_fixed="Y",
        ),
        SalaryComponent(
            component_id="HRA",
            component_name="House Rent Allowance",
            component_type="EARNING",
            taxable="Y",
            calculation_rule="50% of basic",
            is_fixed="Y",
        ),
        SalaryComponent(
            component_id="CONV",
            component_name="Conveyance Allowance",
            component_type="EARNING",
            taxable="Y",
            calculation_rule="Fixed 1600",
            is_fixed="Y",
        ),
        SalaryComponent(
            component_id="MED",
            component_name="Medical Allowance",
            component_type="EARNING",
            taxable="Y",
            calculation_rule="Fixed 1250",
            is_fixed="Y",
        ),
        SalaryComponent(
            component_id="SPECIAL",
            component_name="Special Allowance",
            component_type="EARNING",
            taxable="Y",
            calculation_rule="Balancing figure",
            is_fixed="Y",
        ),
    ]

    db.add_all(components)
    db.flush()

    old_revision = SalaryRevision(
        revision_id="REV002",
        employee_id="SAL002",
        effective_from=date(2025, 1, 1),
        revision_reason="Initial salary",
        previous_annual_fixed=None,
        new_annual_fixed=Decimal("360000.00"),
        pct_change=None,
        role_id_after="ROLE001",
        approved_by=None,
        created_at=datetime.now(),
    )
    db.add(old_revision)
    db.flush()

    old_structure = SalaryStructure(
        structure_id="STRUCT002",
        employee_id="SAL002",
        component_id="BASIC",
        component_name="Basic Salary",
        component_type="EARNING",
        monthly_amount=Decimal("30000.00"),
        effective_from=date(2025, 1, 1),
        effective_to=None,
        revision_id="REV002",
    )
    db.add(old_structure)
    db.commit()

    result = revise_salary(
        db=db,
        employee_id="SAL002",
        effective_date=date(2026, 1, 1),
        new_annual_fixed=Decimal("420000.00"),
        revision_reason="Annual salary increase",
        role_id_after="ROLE001",
        approved_by="HR",
    )

    db.refresh(old_structure)

    assert result.revision_id is not None
    assert result.new_annual_fixed == Decimal("420000.00")
    assert old_structure.effective_to == date(2025, 12, 31)

    new_structures = (
        db.query(SalaryStructure)
        .filter(
            SalaryStructure.employee_id == "SAL002",
            SalaryStructure.effective_from == date(2026, 1, 1),
        )
        .all()
    )

    assert len(new_structures) == 5

    amounts = {
        item.component_id: Decimal(str(item.monthly_amount))
        for item in new_structures
    }

    assert amounts["BASIC"] == Decimal("14000.00")
    assert amounts["HRA"] == Decimal("7000.00")
    assert amounts["CONV"] == Decimal("1600.00")
    assert amounts["MED"] == Decimal("1250.00")
    assert amounts["SPECIAL"] == Decimal("11150.00")

    total_monthly_salary = sum(
        amounts.values(),
        Decimal("0.00"),
    )

    assert total_monthly_salary == Decimal("35000.00")