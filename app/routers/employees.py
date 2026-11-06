from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee
from ..schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from ..security import get_current_user, require_roles


router = APIRouter(prefix="/employees", tags=["employees"])


# 1. GET: List employees (ADMIN and HR only)
@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    search: str | None = None,
    department_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    query = db.query(Employee)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Employee.emp_id.ilike(search_term),
                Employee.full_name.ilike(search_term),
                Employee.work_email.ilike(search_term),
            )
        )

    if department_id:
        query = query.filter(Employee.department_id == department_id)

    return (
        query.order_by(Employee.emp_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


# 2. GET: Get one employee (employees can view only themselves)
@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(
    emp_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "EMPLOYEE" and current_user.employee_id != emp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees can access only their own profile",
        )

    if current_user.role not in ("ADMIN", "HR", "EMPLOYEE"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    employee = db.get(Employee, emp_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee


# 3. POST: Create employee (ADMIN and HR only)
@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    existing_employee = db.get(Employee, employee_data.emp_id)

    if existing_employee is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee ID already exists",
        )

    if employee_data.manager_id == employee_data.emp_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An employee cannot be their own manager",
        )

    employee = Employee(**employee_data.model_dump())
    db.add(employee)

    try:
        db.commit()
        db.refresh(employee)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create employee. Check department, role, and manager IDs.",
        )

    return employee


# 4. PATCH: Update employee (ADMIN and HR only)
@router.patch("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: str,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = db.get(Employee, emp_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    updates = employee_data.model_dump(exclude_unset=True)

    if updates.get("manager_id") == emp_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An employee cannot be their own manager",
        )

    for field, value in updates.items():
        setattr(employee, field, value)

    try:
        db.commit()
        db.refresh(employee)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update employee. Check the supplied values and related IDs.",
        )

    return employee


# 5. DELETE: Deactivate employee (ADMIN and HR only)
@router.delete("/{emp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    emp_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    employee = db.get(Employee, emp_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    if employee.exit_date is None:
        employee.exit_date = date.today()

    employee.employment_status = "Inactive"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not deactivate employee",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# 6. GET: Get an employee's team (ADMIN and HR only)
@router.get("/{emp_id}/team", response_model=list[EmployeeResponse])
def get_employee_team(
    emp_id: str,
    include_former: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    manager = db.get(Employee, emp_id)

    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manager not found",
        )

    query = db.query(Employee).filter(Employee.manager_id == emp_id)

    if not include_former:
        query = query.filter(Employee.exit_date.is_(None))

    return query.order_by(Employee.emp_id).all()