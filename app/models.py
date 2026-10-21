from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100))
    cost_center: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"), index=True
    )
    role_title: Mapped[str] = mapped_column(String(100))
    level: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(20))
    band_min_annual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    band_mid_annual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    band_max_annual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    overtime_eligible: Mapped[bool] = mapped_column(Boolean)
    band_year: Mapped[int] = mapped_column(Integer)


class Employee(Base):
    __tablename__ = "employees"

    emp_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    fname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200))
    work_email: Mapped[str] = mapped_column(String(200))
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    hire_date: Mapped[date] = mapped_column(Date)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(String(50))
    employment_type: Mapped[str] = mapped_column(String(50))

    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.department_id"), nullable=True, index=True
    )
    role_id: Mapped[str | None] = mapped_column(
        ForeignKey("roles.role_id"), nullable=True
    )
    manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.emp_id"), nullable=True, index=True
    )

    work_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    work_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    highest_edu: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prior_experience_year: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    career_gap_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commute_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    pf_applicable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    esi_applicable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resignation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exit_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"

    assignment_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.emp_id"), index=True
    )
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"), index=True
    )
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.role_id"))
    job_level: Mapped[int] = mapped_column(Integer)
    manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.emp_id"), nullable=True, index=True
    )
    change_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    __table_args__ = (
        Index(
            "ix_assignment_employee_dates",
            "employee_id",
            "effective_from",
            "effective_to",
        ),
    )