from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ==============================
# DEPARTMENT SCHEMA
# ==============================

class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_id: str
    department_name: str
    cost_center: str
    description: str | None = None


# ==============================
# EMPLOYEE SCHEMAS
# ==============================

class EmployeeCreate(BaseModel):
    emp_id: str = Field(min_length=1, max_length=10)
    fname: str | None = None
    lname: str | None = None
    full_name: str = Field(min_length=1, max_length=200)
    work_email: str = Field(min_length=1, max_length=200)
    hire_date: date
    employment_status: str = Field(min_length=1, max_length=50)
    employment_type: str = Field(min_length=1, max_length=50)
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    work_location: str | None = None
    work_mode: str | None = None


class EmployeeUpdate(BaseModel):
    fname: str | None = None
    lname: str | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    work_email: str | None = Field(default=None, min_length=1, max_length=200)
    employment_status: str | None = None
    employment_type: str | None = None
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    work_location: str | None = None
    work_mode: str | None = None
    exit_date: date | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emp_id: str
    fname: str | None = None
    lname: str | None = None
    full_name: str
    work_email: str
    hire_date: date
    exit_date: date | None = None
    employment_status: str
    employment_type: str
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    work_location: str | None = None
    work_mode: str | None = None


# ==============================
# SALARY STRUCTURE SCHEMA
# ==============================

class SalaryStructureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    structure_id: str
    employee_id: str
    component_id: str
    component_name: str
    component_type: str
    monthly_amount: Decimal
    effective_from: date
    effective_to: date | None = None
    revision_id: str


# ==============================
# SALARY REVISION SCHEMA
# ==============================

class SalaryRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_id: str
    employee_id: str
    effective_from: date
    revision_reason: str
    previous_annual_fixed: Decimal | None = None
    new_annual_fixed: Decimal
    pct_change: Decimal | None = None
    role_id_after: str
    approved_by: str | None = None