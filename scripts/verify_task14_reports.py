from datetime import date
from sqlalchemy import func
from app.database import SessionLocal
from app.models import PayrollRun, PayrollItem

db = SessionLocal()

start_date = date(2026, 4, 1)
end_date = date(2026, 5, 1)

try:
    result = (
        db.query(
            func.count(func.distinct(PayrollItem.employee_id)),
            func.sum(PayrollItem.pf_employee),
            func.sum(PayrollItem.pf_employer),
            func.sum(PayrollItem.esi_employee),
            func.sum(PayrollItem.esi_employer),
            func.sum(PayrollItem.tds),
            func.sum(PayrollItem.professional_tax),
            func.sum(
                PayrollItem.earned_fixed_pay
                + PayrollItem.overtime_pay
                + PayrollItem.variable_pay
            ),
        )
        .join(PayrollRun, PayrollRun.run_id == PayrollItem.run_id)
        .filter(
            PayrollRun.period_start >= start_date,
            PayrollRun.period_start < end_date,
            PayrollRun.status.in_([
                "PAID",
                "POSTED - PAYMENT PENDING"
            ]),
        )
        .one()
    )

    labels = [
        "Employee count",
        "Employee PF",
        "Employer PF",
        "Employee ESI",
        "Employer ESI",
        "TDS",
        "Professional tax",
        "Gross pay",
    ]

    print("DIRECT DATABASE VERIFICATION - APRIL 2026")
    for label, value in zip(labels, result):
        print(f"{label}: {value}")

finally:
    db.close()
