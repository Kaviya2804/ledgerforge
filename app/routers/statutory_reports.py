from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PayrollRun, PayrollItem, User
from ..security import require_roles


router = APIRouter(
    prefix="/reports",
    tags=["statutory-reports"],
)


POSTED_STATUSES = [
    "PAID",
    "POSTED - PAYMENT PENDING",
]


@router.get("/statutory/{year}/{month}")
def get_monthly_statutory_report(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "HR")
    ),
):
    """Generate monthly PF, ESI and TDS report."""

    # Explicit role verification
    if current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12",
        )

    # Validate year
    if year < 2000 or year > 2100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid year",
        )

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Fetch saved payroll totals
    result = (
        db.query(
            func.count(
                func.distinct(PayrollItem.employee_id)
            ).label("employee_count"),

            func.coalesce(
                func.sum(PayrollItem.pf_employee), 0
            ).label("pf_employee"),

            func.coalesce(
                func.sum(PayrollItem.pf_employer), 0
            ).label("pf_employer"),

            func.coalesce(
                func.sum(PayrollItem.esi_employee), 0
            ).label("esi_employee"),

            func.coalesce(
                func.sum(PayrollItem.esi_employer), 0
            ).label("esi_employer"),

            func.coalesce(
                func.sum(PayrollItem.tds), 0
            ).label("tds"),

            func.coalesce(
                func.sum(PayrollItem.professional_tax), 0
            ).label("professional_tax"),

            func.coalesce(
                func.sum(
                    PayrollItem.earned_fixed_pay
                    + PayrollItem.overtime_pay
                    + PayrollItem.variable_pay
                ), 0
            ).label("gross_pay"),
        )
        .join(
            PayrollRun,
            PayrollRun.run_id == PayrollItem.run_id,
        )
        .filter(
            PayrollRun.period_start >= start_date,
            PayrollRun.period_start < end_date,
            PayrollRun.status.in_(POSTED_STATUSES),
        )
        .one()
    )

    # Return statutory report
    return {
        "report": "Monthly Statutory Report",
        "period": f"{year}-{month:02d}",
        "employee_count": result.employee_count,

        "pf": {
            "employee_contribution": str(
                result.pf_employee
            ),
            "employer_contribution": str(
                result.pf_employer
            ),
            "total": str(
                result.pf_employee + result.pf_employer
            ),
        },

        "esi": {
            "employee_contribution": str(
                result.esi_employee
            ),
            "employer_contribution": str(
                result.esi_employer
            ),
            "total": str(
                result.esi_employee + result.esi_employer
            ),
        },

        "tds": str(result.tds),

        "professional_tax": str(
            result.professional_tax
        ),

        "gross_pay": str(result.gross_pay),

        "included_statuses": POSTED_STATUSES,
    }