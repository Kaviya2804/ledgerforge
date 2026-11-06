import pandas as pd
from pathlib import Path
from decimal import Decimal
import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Expense, JournalEntry, JournalLine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT.parent / "03_Data" / "csv"

GST_ACCOUNT = "1200"
PAYABLE_ACCOUNT = "2001"
BANK_ACCOUNT = "1001"


def load_expense_data():
    expenses = pd.read_csv(DATA_DIR / "expenses.csv")
    vendors = pd.read_csv(DATA_DIR / "vendors.csv")
    journal_entries = pd.read_csv(DATA_DIR / "journal_entries.csv")

    return expenses, vendors, journal_entries


def find_duplicate_expense(expense, existing_expenses):
    """Find another bill with the same vendor and bill reference."""

    duplicates = existing_expenses[
        (existing_expenses["vendor_id"].astype(str) == str(expense["vendor_id"]))
        & (
            existing_expenses["bill_reference"].astype(str)
            == str(expense["bill_reference"])
        )
        & (
            existing_expenses["expense_id"].astype(str)
            != str(expense["expense_id"])
        )
    ]

    return not duplicates.empty


def create_expense_lines(expense):
    """Create the debit and credit lines for an expense bill."""

    amount = Decimal(str(expense["amount_excl_gst"]))
    gst = Decimal(str(expense["gst_amount"]))
    total = Decimal(str(expense["total_amount"]))

    if amount + gst != total:
        raise ValueError("Expense amount and GST do not match total amount")

    lines = [
        {
            "account_code": str(expense["category_account"]),
            "debit": amount,
            "credit": Decimal("0")
        }
    ]

    if gst > 0:
        lines.append({
            "account_code": GST_ACCOUNT,
            "debit": gst,
            "credit": Decimal("0")
        })

    lines.append({
        "account_code": PAYABLE_ACCOUNT,
        "debit": Decimal("0"),
        "credit": total
    })

    return lines
def approve_expense(expense, approver_id, existing_expenses):
    """Approve a submitted expense and prepare its journal posting."""

    if find_duplicate_expense(expense, existing_expenses):
        raise ValueError("Duplicate expense bill detected")

    if expense["status"].upper() != "SUBMITTED":
        raise ValueError("Only submitted expenses can be approved")

    if str(expense["submitted_by"]) == str(approver_id):
        raise ValueError("Submitter cannot approve their own expense")

    if pd.notna(expense.get("ledger_entry_id")):
        raise ValueError("Expense is already posted")

    lines = create_expense_lines(expense)

    expense["status"] = "APPROVED"
    expense["approved_by"] = str(approver_id)

    return {
        "expense_id": str(expense["expense_id"]),
        "description": f"Expense bill {expense['bill_reference']}",
        "lines": lines
    }
def pay_expense(expense, payment_date, payment_mode="BANK"):
    """Prepare payment lines for an approved expense."""

    if expense["status"].upper() != "APPROVED":
        raise ValueError("Only approved expenses can be paid")

    if pd.notna(expense.get("payment_ledger_entry_id")):
        raise ValueError("Expense payment is already posted")

    total = Decimal(str(expense["total_amount"]))

    if total <= 0:
        raise ValueError("Payment amount must be positive")

    lines = [
        {
            "account_code": PAYABLE_ACCOUNT,
            "debit": total,
            "credit": Decimal("0")
        },
        {
            "account_code": BANK_ACCOUNT,
            "debit": Decimal("0"),
            "credit": total
        }
    ]

    expense["status"] = "PAID"
    expense["paid_date"] = str(payment_date)
    expense["payment_mode"] = payment_mode

    return {
        "expense_id": str(expense["expense_id"]),
        "description": f"Payment for bill {expense['bill_reference']}",
        "lines": lines
    }
def generate_vendor_spend_report(expenses):
    """Summarize expense spending by vendor and month."""

    report_data = expenses.copy()

    report_data["expense_date"] = pd.to_datetime(
        report_data["expense_date"]
    )

    report_data["month"] = (
        report_data["expense_date"].dt.to_period("M").astype(str)
    )

    report = (
        report_data[report_data["status"].str.upper().isin(["PAID", "UNPAID"])]
        .groupby(["vendor_id", "month"], as_index=False)
        .agg(
            bill_count=("expense_id", "count"),
            total_spend=("total_amount", "sum")
        )
    )

    return report
def create_db_journal(db, expense, source_type, description, lines):
    entry_id = f"EXP-{uuid.uuid4().hex[:12].upper()}"

    total_debit = sum(line["debit"] for line in lines)
    total_credit = sum(line["credit"] for line in lines)

    if total_debit != total_credit:
        raise ValueError("Journal entry is not balanced")

    entry = JournalEntry(
        entry_id=entry_id,
        entry_date=date.today(),
        description=description,
        source_type=source_type,
        source_id=expense.expense_id,
        status="POSTED",
        total_debit=total_debit,
        total_credit=total_credit,
        created_by=expense.submitted_by
    )

    for number, line in enumerate(lines, start=1):
        entry.lines.append(
            JournalLine(
                line_no=number,
                account_code=line["account_code"],
                debit=line["debit"],
                credit=line["credit"],
                line_description=description
            )
        )

    db.add(entry)
    db.flush()

    return entry_id
def approve_expense_db(db: Session, expense_id: str, approver_id: str):
    expense = db.query(Expense).filter_by(expense_id=expense_id).first()

    if expense is None:
        raise ValueError("Expense not found")

    if expense.status.upper() != "SUBMITTED":
        raise ValueError("Only submitted expenses can be approved")

    if expense.submitted_by == approver_id:
        raise ValueError("Submitter cannot approve their own expense")

    if expense.ledger_entry_id:
        raise ValueError("Expense is already posted")

    existing = db.query(JournalEntry).filter_by(
        source_type="EXPENSE",
        source_id=expense_id
    ).first()

    if existing:
        raise ValueError("Expense journal already exists")

    lines = create_expense_lines({
        "category_account": expense.category_account,
        "amount_excl_gst": expense.amount_excl_gst,
        "gst_amount": expense.gst_amount,
        "total_amount": expense.total_amount
    })

    try:
        entry_id = create_db_journal(
            db, expense, "EXPENSE",
            f"Expense bill {expense.bill_reference}", lines
        )

        expense.status = "APPROVED"
        expense.approved_by = approver_id
        expense.ledger_entry_id = entry_id

        db.commit()
        return entry_id

    except Exception:
        db.rollback()
        raise
def pay_expense_db(
    db: Session,
    expense_id: str,
    payment_date: date,
    payment_mode: str = "BANK"
):
    expense = db.query(Expense).filter_by(
        expense_id=expense_id
    ).first()

    if expense is None:
        raise ValueError("Expense not found")

    if expense.status.upper() != "APPROVED":
        raise ValueError("Only approved expenses can be paid")

    if expense.payment_ledger_entry_id:
        raise ValueError("Expense payment is already posted")

    total = Decimal(str(expense.total_amount))

    if total <= 0:
        raise ValueError("Payment amount must be positive")

    lines = [
        {
            "account_code": PAYABLE_ACCOUNT,
            "debit": total,
            "credit": Decimal("0")
        },
        {
            "account_code": BANK_ACCOUNT,
            "debit": Decimal("0"),
            "credit": total
        }
    ]

    try:
        entry_id = create_db_journal(
            db,
            expense,
            "EXPENSE_PAYMENT",
            f"Payment for bill {expense.bill_reference}",
            lines
        )

        expense.status = "PAID"
        expense.paid_date = payment_date
        expense.payment_mode = payment_mode
        expense.payment_ledger_entry_id = entry_id

        db.commit()
        return entry_id

    except Exception:
        db.rollback()
        raise