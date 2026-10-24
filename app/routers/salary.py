from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Employee, SalaryRevision
from ..schemas import (
    SalaryStructureResponse,
    SalaryRevisionResponse,
)
from ..salary_service import get_structure


router = APIRouter(prefix="/salary", tags=["salary"])


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
):
    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    structures = get_structure(
        db=db,
        employee_id=employee_id,
        target_date=target_date,
    )

    if not structures:
        raise HTTPException(
            status_code=404,
            detail="No salary structure found for this date",
        )

    return structures


@router.get(
    "/{employee_id}/history",
    response_model=list[SalaryRevisionResponse],
)
def get_salary_revision_history(
    employee_id: str,
    db: Session = Depends(get_db),
):
    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    revisions = (
        db.query(SalaryRevision)
        .filter(
            SalaryRevision.employee_id == employee_id
        )
        .order_by(
            SalaryRevision.effective_from.desc()
        )
        .all()
    )

    return revisions