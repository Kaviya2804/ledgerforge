from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from ..database import get_db
from ..models import PayrollRun
from ..celery_app import celery_app
from ..tasks import process_bulk_payroll
from ..security import get_current_user

router = APIRouter(prefix="/payroll-jobs", tags=["payroll-jobs"])


@router.post("/process")
def start_bulk_payroll(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN and HR can process payroll jobs",
        )

    runs = (
        db.query(PayrollRun)
        .filter(PayrollRun.run_id.like("BULK-%"))
        .order_by(PayrollRun.period_start)
        .all()
    )

    if len(runs) != 18:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 18 payroll runs, found {len(runs)}",
        )

    if any(run.status != "DRAFT" for run in runs):
        raise HTTPException(
            status_code=400,
            detail="All 18 payroll runs must be in DRAFT status",
        )

    run_ids = [run.run_id for run in runs]

    task = process_bulk_payroll.delay(run_ids)

    return {
        "message": "Bulk payroll job submitted",
        "task_id": task.id,
        "total_runs": len(run_ids),
        "status": "QUEUED",
    }


@router.get("/{task_id}")
def get_payroll_job_status(
    task_id: str,
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN and HR can view payroll jobs",
        )

    task = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": task.state,
        "progress": task.info if task.state == "PROGRESS" else None,
        "result": task.result if task.ready() else None,
    }