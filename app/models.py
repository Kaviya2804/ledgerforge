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
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship



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
class Client(Base):
    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_or_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gst_registration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_terms_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_behaviour: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_service_line: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    onboarded_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(50))
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.client_id"), index=True)
    invoice_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    service_line_account: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(10))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_rate_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    balance_due: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(30))
    last_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    carried_in_from_prior_period: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ledger_entry_id: Mapped[str | None] = mapped_column(String(30), nullable=True)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    invoice_item_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.invoice_id"), index=True)
    line_no: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    revenue_account: Mapped[str] = mapped_column(String(20))


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    payment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.invoice_id"), index=True)
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_mode: Mapped[str] = mapped_column(String(50))
    reference_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ledger_entry_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(200))
    primary_expense_account: Mapped[str] = mapped_column(String(20))
    payment_terms_days: Mapped[int] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gst_registration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    expense_date: Mapped[date] = mapped_column(Date)
    category_account: Mapped[str] = mapped_column(String(20))
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.vendor_id"), index=True)
    bill_reference: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300))
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.department_id"), nullable=True
    )
    amount_excl_gst: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gst_rate_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    due_date: Mapped[date] = mapped_column(Date)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    payment_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(20))
    approved_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ledger_entry_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    payment_ledger_entry_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
class JournalEntry(Base):
    __tablename__ = "journal_entries"

    entry_id = Column(String(30), primary_key=True)
    entry_date = Column(Date, nullable=False)
    description = Column(String(300), nullable=False)
    source_type = Column(String(30), nullable=False)
    source_id = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    total_debit = Column(Numeric(14, 2), nullable=False)
    total_credit = Column(Numeric(14, 2), nullable=False)
    created_by = Column(String(20), nullable=False)

    lines = relationship(
        "JournalLine",
        back_populates="entry",
        cascade="all, delete-orphan"
    )
class JournalLine(Base):
    __tablename__ = "journal_lines"

    line_id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(
        String(30),
        ForeignKey("journal_entries.entry_id"),
        nullable=False
    )
    line_no = Column(Integer, nullable=False)
    account_code = Column(String(20), nullable=False)
    debit = Column(Numeric(14, 2), nullable=False)
    credit = Column(Numeric(14, 2), nullable=False)
    line_description = Column(String(300))

    entry = relationship("JournalEntry", back_populates="lines")
class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
    )

    run_id = Column(String(30), primary_key=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=True)

    employees_paid = Column(Integer, nullable=False)
    total_gross = Column(Numeric(14, 2), nullable=False)
    total_deductions = Column(Numeric(14, 2), nullable=False)
    total_net = Column(Numeric(14, 2), nullable=False)
    total_employer_contributions = Column(Numeric(14, 2), nullable=False)
    total_employer_cost = Column(Numeric(14, 2), nullable=False)

    status = Column(String(20), nullable=False)
    run_by = Column(String(20), nullable=False)
    approved_by = Column(String(20))
    created_at = Column(DateTime, nullable=False)
    approved_at = Column(DateTime)

    idempotency_key = Column(String(100), nullable=False)
    journal_entry_id = Column(
        String(30),
        ForeignKey("journal_entries.entry_id")
    )
    calculation_version = Column(String(50), nullable=False)
class PayrollItem(Base):
    __tablename__ = "payroll_items"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id"),
    )

    payroll_item_id = Column(String(30), primary_key=True)
    run_id = Column(String(30), ForeignKey("payroll_runs.run_id"), nullable=False)
    employee_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)
    department_id = Column(String(10), ForeignKey("departments.department_id"), nullable=False)

    earned_fixed_pay = Column(Numeric(14, 2), nullable=False)
    overtime_pay = Column(Numeric(14, 2), nullable=False)
    variable_pay = Column(Numeric(14, 2), nullable=False)
    pf_employer = Column(Numeric(14, 2), nullable=False)
    esi_employer = Column(Numeric(14, 2), nullable=False)
    pf_employee = Column(Numeric(14, 2), nullable=False, default=0)
    esi_employee = Column(Numeric(14, 2), nullable=False, default=0)
    professional_tax = Column(Numeric(14, 2), nullable=False, default=0)
    tds = Column(Numeric(14, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(14, 2), nullable=False, default=0)
    net_pay = Column(Numeric(14, 2), nullable=False, default=0)
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(20), primary_key=True)

    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.emp_id"),
        nullable=False,
        unique=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
class TaxSlab(Base):
    __tablename__ = "tax_slabs"

    slab_id = Column(String(20), primary_key=True)
    regime = Column(String(10), nullable=False)
    financial_year = Column(String(20), nullable=False)
    income_from = Column(Numeric(14, 2), nullable=False)
    income_to = Column(Numeric(14, 2), nullable=True)
    rate_percent = Column(Numeric(6, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    note = Column(String(300), nullable=True)


class TaxParameter(Base):
    __tablename__ = "tax_parameters"

    parameter = Column(String(100), primary_key=True)
    value = Column(Numeric(14, 2), nullable=False)
    note = Column(String(300), nullable=True)


class StatutoryRate(Base):
    __tablename__ = "statutory_rates"

    parameter = Column(String(100), primary_key=True)
    value = Column(Numeric(14, 2), nullable=False)
    unit = Column(String(50), nullable=True)
    note = Column(String(300), nullable=True)
    effective_from = Column(Date, nullable=False)

