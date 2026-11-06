from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import require_roles
from ..financial_reports_service import (
    get_trial_balance,
    get_profit_loss,
    get_balance_sheet,
)


router = APIRouter(
    prefix="/reports/financial",
    tags=["financial-reports"],
)


@router.get("/trial-balance")
def trial_balance(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "HR")),
):
    try:
        return get_trial_balance(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/profit-loss")
def profit_loss(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "HR")),
):
    try:
        return get_profit_loss(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/balance-sheet")
def balance_sheet(
    as_of_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "HR")),
):
    try:
        return get_balance_sheet(as_of_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))