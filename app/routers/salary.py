from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee, SalaryRevision
from ..schemas import (
    SalaryStructureResponse,
    SalaryRevisionResponse,
)
from ..salary_service import get_structure
from ..security import get_current_user


router = APIRouter(prefix="/salary", tags=["salary"])


def check_salary_access(employee_id: str, current_user):
    if current_user.role == "EMPLOYEE":
        if current_user.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can access only their own salary information",
            )

    elif current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


# 1. GET: Employee salary structure
@router.get(
    "/{employee_id}/structure",
    response_model=list[SalaryStructureResponse],
)
def get_employee_salary_structure(
    employee_id: str,
    target_date: date = Query(
        default_factory=date.today,
        alias="date",
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_salary_access(employee_id, current_user)

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    structures = get_structure(
        db=db,
        employee_id=employee_id,
        target_date=target_date,
    )

    if not structures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No salary structure found for this date",
        )

    return structures


# 2. GET: Salary revision history
@router.get(
    "/{employee_id}/history",
    response_model=list[SalaryRevisionResponse],
)
def get_salary_revision_history(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_salary_access(employee_id, current_user)

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    revisions = (
        db.query(SalaryRevision)
        .filter(SalaryRevision.employee_id == employee_id)
        .order_by(SalaryRevision.effective_from.desc())
        .all()
    )

    return revisions