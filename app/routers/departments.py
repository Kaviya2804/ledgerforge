"""Department API routes with role-based access."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Department
from ..schemas import DepartmentOut
from ..security import require_roles

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    return db.query(Department).order_by(
        Department.department_id
    ).all()


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "HR")),
):
    department = db.get(Department, department_id)

    if not department:
        raise HTTPException(404, "Department not found")

    return department
