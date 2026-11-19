from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import PayrollRun
from app.payroll_run_service import process_payroll_run


@celery_app.task(bind=True, name="app.tasks.process_bulk_payroll")
def process_bulk_payroll(self, run_ids: list[str]):
    db = SessionLocal()
    total = len(run_ids)
    completed = 0

    try:
        if total != 18:
            raise ValueError("Expected exactly 18 payroll runs")

        for run_id in run_ids:
            run = db.get(PayrollRun, run_id)

            if run is None or run.status != "DRAFT":
                raise ValueError(
                    f"Payroll run {run_id} is missing or not in DRAFT status"
                )

            process_payroll_run(db, run_id)
            db.commit()

            completed += 1
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": completed,
                    "total": total,
                    "percent": round(completed / total * 100, 2),
                    "run_id": run_id,
                },
            )

        return {
            "status": "completed",
            "processed": completed,
            "total": total,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
