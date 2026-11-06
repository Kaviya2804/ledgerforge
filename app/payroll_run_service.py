from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    PayrollRun,
    PayrollItem,
    JournalEntry,
    JournalLine,
    TaxSlab,
    TaxParameter,
    StatutoryRate,
)

from app.payroll_service import (
    calculate_employee_month,
    get_active_assignment,
    load_csv_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT.parent / "03_Data" / "csv"


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def decimal_sum(results, field):
    return money(
        sum(
            (Decimal(str(result[field])) for result, _ in results),
            Decimal("0"),
        )
    )


def process_payroll_run(db: Session, run_id: str):

    # 1. Find payroll run
    run = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if not run:
        raise ValueError("Payroll run not found")

    if run.status != "DRAFT":
        raise ValueError(
            f"Cannot process payroll. Current status: {run.status}"
        )

    # 2. Load company data from CSV
    employees = load_csv_rows(DATA_FOLDER / "employees.csv")
    assignments = load_csv_rows(DATA_FOLDER / "employee_assignments.csv")
    roles = load_csv_rows(DATA_FOLDER / "roles.csv")
    salary_rows = load_csv_rows(DATA_FOLDER / "salary_structures.csv")
    attendance_rows = load_csv_rows(DATA_FOLDER / "attendance.csv")

    # 3. Load statutory rules from DATABASE
    statutory_rates = {
        row.parameter: row.value
        for row in db.query(StatutoryRate).all()
    }

    # 4. Load tax parameters from DATABASE
    tax_parameters = {
        row.parameter: row.value
        for row in db.query(TaxParameter).all()
    }

    # 5. Determine financial year
    tax_year = (
        "FY2025-26"
        if run.period_start < date(2026, 4, 1)
        else "FY2026-27"
    )

    # 6. Load NEW regime slabs from DATABASE
    tax_slabs = [
        {
            "income_from": row.income_from,
            "income_to": row.income_to,
            "rate": row.rate_percent / Decimal("100"),
        }
        for row in (
            db.query(TaxSlab)
            .filter(
                TaxSlab.financial_year == tax_year,
                TaxSlab.regime == "NEW",
                TaxSlab.effective_from <= run.period_start,
            )
            .order_by(TaxSlab.income_from)
            .all()
        )
    ]

    if not tax_slabs:
        raise ValueError(
            f"No tax slabs configured for {tax_year}"
        )

    if not statutory_rates or not tax_parameters:
        raise ValueError("Tax or statutory rules are missing")

    # 7. Calculate employee payroll
    payroll_results = []

    for employee in employees:
        employee_id = employee["employee_id"]

        try:
            result = calculate_employee_month(
                employee_id=employee_id,
                period_start=run.period_start,
                period_end=run.period_end,
                employees=employees,
                assignments=assignments,
                roles=roles,
                salary_rows=salary_rows,
                attendance_rows=attendance_rows,
                statutory_rates=statutory_rates,
                tax_parameters=tax_parameters,
                tax_slabs=tax_slabs,
            )

            assignment = get_active_assignment(
                assignments,
                employee_id,
                run.period_start,
                run.period_end,
                employee.get("exit_date"),
            )

            payroll_results.append(
                (result, assignment["department_id"])
            )

        except ValueError:
            continue

    if not payroll_results:
        raise ValueError("No eligible employees found")

    # 8. Calculate totals
    total_gross = decimal_sum(payroll_results, "gross_pay")
    total_deductions = decimal_sum(
        payroll_results, "total_deductions"
    )
    total_net = decimal_sum(payroll_results, "net_pay")
    total_pf = decimal_sum(payroll_results, "pf_employer")
    total_esi = decimal_sum(payroll_results, "esi_employer")
    total_employer_cost = decimal_sum(
        payroll_results, "employer_cost"
    )

    # 9. Save employee payroll items
    for number, (result, department_id) in enumerate(
        payroll_results,
        start=1,
    ):
        db.add(
            PayrollItem(
                payroll_item_id=f"{run_id}-ITEM-{number:05d}",
                run_id=run_id,
                employee_id=result["employee_id"],
                department_id=department_id,
                earned_fixed_pay=result["earned_fixed_pay"],
                overtime_pay=result["overtime_pay"],
                variable_pay=result["variable_pay"],
                pf_employer=result["pf_employer"],
                esi_employer=result["esi_employer"],
                pf_employee=result["pf_employee"],
                esi_employee=result["esi_employee"],
                professional_tax=result["professional_tax"],
                tds=result["tds"],
                other_deductions=result["other_deductions"],
                net_pay=result["net_pay"],
            )
        )

    # 10. Update payroll run
    run.employees_paid = len(payroll_results)
    run.total_gross = total_gross
    run.total_deductions = total_deductions
    run.total_net = total_net
    run.total_employer_contributions = money(total_pf + total_esi)
    run.total_employer_cost = total_employer_cost
    run.status = "PROCESSED"

    db.flush()

    return run


def create_draft_payroll_run(
    db: Session,
    run_id: str,
    period_start: date,
    period_end: date,
    run_by: str,
):

    existing = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if existing:
        raise ValueError("Payroll run already exists")

    idempotency_key = f"PAYROLL-{period_start}-{period_end}"

    duplicate = (
        db.query(PayrollRun)
        .filter_by(idempotency_key=idempotency_key)
        .first()
    )

    if duplicate:
        raise ValueError("Payroll period already exists")

    run = PayrollRun(
        run_id=run_id,
        period_start=period_start,
        period_end=period_end,
        pay_date=None,
        employees_paid=0,
        total_gross=money(0),
        total_deductions=money(0),
        total_net=money(0),
        total_employer_contributions=money(0),
        total_employer_cost=money(0),
        status="DRAFT",
        run_by=run_by,
        created_at=datetime.now(),
        idempotency_key=idempotency_key,
        calculation_version="task14-v1",
    )

    db.add(run)
    db.flush()

    return run


def approve_payroll_run(
    db: Session,
    run_id: str,
    approved_by: str,
):

    run = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if not run:
        raise ValueError("Payroll run not found")

    if run.status != "PROCESSED":
        raise ValueError(
            f"Cannot approve payroll. Current status: {run.status}"
        )

    if run.run_by == approved_by:
        raise ValueError("Payroll creator cannot approve their own run")

    run.status = "APPROVED"
    run.approved_by = approved_by
    run.approved_at = datetime.now()

    db.flush()

    return run


def post_payroll_run(db: Session, run_id: str):

    from collections import defaultdict

    run = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if not run:
        raise ValueError("Payroll run not found")

    if run.status != "APPROVED":
        raise ValueError("Only approved payroll runs can be posted")

    existing = (
        db.query(JournalEntry)
        .filter_by(source_type="PAYROLL_RUN", source_id=run_id)
        .first()
    )

    if run.journal_entry_id or existing:
        raise ValueError("Payroll run is already posted")

    items = db.query(PayrollItem).filter_by(run_id=run_id).all()

    if not items:
        raise ValueError("No payroll items found")

    department_totals = defaultdict(lambda: defaultdict(Decimal))
    totals = defaultdict(Decimal)

    for item in items:

        department_id = item.department_id

        for field, account in [
            ("earned_fixed_pay", "5001"),
            ("overtime_pay", "5002"),
            ("variable_pay", "5003"),
            ("pf_employer", "5004"),
            ("esi_employer", "5005"),
        ]:
            amount = money(getattr(item, field))
            department_totals[department_id][account] += amount

        for field in [
            "net_pay",
            "pf_employee",
            "esi_employee",
            "professional_tax",
            "tds",
            "other_deductions",
            "pf_employer",
            "esi_employer",
        ]:
            totals[field] += money(getattr(item, field))

    lines = []

    for department_id, amounts in department_totals.items():
        for account_code, amount in amounts.items():

            if amount > 0:
                lines.append(
                    JournalLine(
                        line_no=len(lines) + 1,
                        account_code=account_code,
                        debit=amount,
                        credit=money(0),
                        line_description=(
                            f"Payroll expense - Department {department_id}"
                        ),
                    )
                )

    liabilities = [
        ("2100", totals["net_pay"]),
        ("2110", totals["pf_employee"] + totals["pf_employer"]),
        ("2120", totals["esi_employee"] + totals["esi_employer"]),
        ("2130", totals["tds"]),
        ("2140", totals["professional_tax"]),
        ("1300", totals["other_deductions"]),
    ]

    for account_code, amount in liabilities:

        if amount > 0:
            lines.append(
                JournalLine(
                    line_no=len(lines) + 1,
                    account_code=account_code,
                    debit=money(0),
                    credit=amount,
                    line_description=f"Payroll liability - {account_code}",
                )
            )

    total_debit = sum(
        (money(line.debit) for line in lines),
        Decimal("0"),
    )

    total_credit = sum(
        (money(line.credit) for line in lines),
        Decimal("0"),
    )

    if total_debit != total_credit:
        raise ValueError(
            f"Payroll journal is unbalanced: "
            f"Debit {total_debit}, Credit {total_credit}"
        )

    expected_total = money(run.total_employer_cost)

    if total_debit != expected_total:
        raise ValueError(
            f"Payroll journal does not match employer cost: "
            f"Journal {total_debit}, Expected {expected_total}"
        )

    entry_id = f"PR-{run_id}"

    entry = JournalEntry(
        entry_id=entry_id,
        entry_date=run.pay_date or run.period_end,
        description=f"Payroll posting for {run.run_id}",
        source_type="PAYROLL_RUN",
        source_id=run.run_id,
        status="POSTED",
        total_debit=total_debit,
        total_credit=total_credit,
        created_by=run.approved_by,
        lines=lines,
    )

    db.add(entry)
    db.flush()

    run.journal_entry_id = entry_id
    db.flush()

    return entry


def reverse_payroll_run(
    db: Session,
    run_id: str,
    reversed_by: str,
):

    run = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if not run:
        raise ValueError("Payroll run not found")

    if run.status not in ["APPROVED", "PAID"]:
        raise ValueError("Only posted payroll runs can be reversed")

    if not run.journal_entry_id:
        raise ValueError("No original journal entry linked")

    existing_reversal = (
        db.query(JournalEntry)
        .filter_by(
            source_type="PAYROLL_REVERSAL",
            source_id=run_id,
        )
        .first()
    )

    if existing_reversal:
        raise ValueError("Payroll run is already reversed")

    original = (
        db.query(JournalEntry)
        .filter_by(entry_id=run.journal_entry_id)
        .first()
    )

    if not original:
        raise ValueError("Original journal entry not found")

    reversal_lines = []

    for line in original.lines:
        reversal_lines.append(
            JournalLine(
                line_no=len(reversal_lines) + 1,
                account_code=line.account_code,
                debit=money(line.credit),
                credit=money(line.debit),
                line_description=f"Reversal - {line.line_description}",
            )
        )

    reversal_id = f"REV-{run_id}"

    reversal = JournalEntry(
        entry_id=reversal_id,
        entry_date=run.period_end,
        description=f"Reversal of payroll {run_id}",
        source_type="PAYROLL_REVERSAL",
        source_id=run_id,
        status="POSTED",
        total_debit=money(original.total_credit),
        total_credit=money(original.total_debit),
        created_by=reversed_by,
        lines=reversal_lines,
    )

    db.add(reversal)
    db.flush()

    run.status = "REVERSED"
    db.flush()

    return reversal


def mark_payroll_paid(
    db: Session,
    run_id: str,
    pay_date: date,
):

    run = db.query(PayrollRun).filter_by(run_id=run_id).first()

    if not run:
        raise ValueError("Payroll run not found")

    if run.status != "APPROVED":
        raise ValueError("Only approved payroll runs can be marked as paid")

    if not run.journal_entry_id:
        raise ValueError("Payroll must be posted to the ledger before payment")

    entry = (
        db.query(JournalEntry)
        .filter_by(entry_id=run.journal_entry_id)
        .first()
    )

    if not entry or entry.status != "POSTED":
        raise ValueError("Posted journal entry not found")

    run.pay_date = pay_date
    run.status = "PAID"

    db.flush()

    return run