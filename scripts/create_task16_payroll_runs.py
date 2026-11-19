from datetime import date
from app.database import SessionLocal
from app.payroll_run_service import create_draft_payroll_run

db = SessionLocal()

try:
    created = []

    for year, month in [
        (2025, 4), (2025, 5), (2025, 6), (2025, 7),
        (2025, 8), (2025, 9), (2025, 10), (2025, 11),
        (2025, 12), (2026, 1), (2026, 2), (2026, 3),
        (2026, 4), (2026, 5), (2026, 6), (2026, 7),
        (2026, 8), (2026, 9)
    ]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            from calendar import monthrange
            end = date(year, month, monthrange(year, month)[1])

        run_id = f"BULK-{year}-{month:02d}"

        run = create_draft_payroll_run(
            db=db,
            run_id=run_id,
            period_start=start,
            period_end=end,
            run_by="U-0099",
        )
        created.append(run.run_id)

    db.commit()
    print("Created payroll runs:", len(created))
    print(created)

except Exception:
    db.rollback()
    raise
finally:
    db.close()
