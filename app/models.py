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
class SalaryComponent(Base):
    __tablename__ = "salary_components"

    component_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    component_name: Mapped[str] = mapped_column(String(100))
    component_type: Mapped[str] = mapped_column(String(30))
    taxable: Mapped[str] = mapped_column(String(1))
    calculation_rule: Mapped[str] = mapped_column(String(300))
    is_fixed: Mapped[str] = mapped_column(String(1))


class SalaryRevision(Base):
    __tablename__ = "salary_revisions"

    revision_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.emp_id"), index=True)
    effective_from: Mapped[date] = mapped_column(Date, index=True)
    revision_reason: Mapped[str] = mapped_column(String(200))
    previous_annual_fixed: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    new_annual_fixed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    pct_change: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    role_id_after: Mapped[str] = mapped_column(ForeignKey("roles.role_id"))
    approved_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    structure_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.emp_id"), index=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("salary_components.component_id"))
    component_name: Mapped[str] = mapped_column(String(100))
    component_type: Mapped[str] = mapped_column(String(30))
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    effective_from: Mapped[date] = mapped_column(Date, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("salary_revisions.revision_id"))

    __table_args__ = (
        Index("ix_salary_employee_dates", "employee_id", "effective_from", "effective_to"),

    )
class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.emp_id"), index=True
    )
    attendance_date: Mapped[date] = mapped_column(Date, index=True)
    weekday: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))
    leave_type_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    check_in: Mapped[str | None] = mapped_column(String(10), nullable=True)
    check_out: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hours_worked: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    overtime_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    late_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_quality_flag: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.department_id"), nullable=True, index=True
    )
class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_code: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )
    leave_type_name: Mapped[str] = mapped_column(String(100))
    pay_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    annual_quota_days: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    prorated_for_joiners: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    carry_forward_allowed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    max_carry_forward_days: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    policy_note: Mapped[str | None] = mapped_column(
        String(300), nullable=True
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    leave_request_id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.emp_id"), index=True
    )
    leave_type_code: Mapped[str] = mapped_column(
        ForeignKey("leave_types.leave_type_code")
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    days: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    applied_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    approver_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    decided_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.emp_id"), primary_key=True
    )
    as_of_date: Mapped[date] = mapped_column(Date, primary_key=True)
    financial_year: Mapped[str] = mapped_column(String(20))
    cl_entitlement: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    cl_used: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    cl_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    sl_entitlement: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    sl_used: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    sl_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    el_used_fy: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    el_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )
    pending_days: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2), nullable=True
    )


class Holiday(Base):
    __tablename__ = "holidays"

    holiday_date: Mapped[date] = mapped_column(Date, primary_key=True)
    holiday_name: Mapped[str] = mapped_column(String(100))
    holiday_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weekday: Mapped[str | None] = mapped_column(String(10), nullable=True)
    falls_on_weekend: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    calendar_note: Mapped[str | None] = mapped_column(
        String(300), nullable=True
    )
