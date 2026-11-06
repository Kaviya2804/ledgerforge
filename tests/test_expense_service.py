import pandas as pd
import pytest

from app.expense_service import (
    find_duplicate_expense,
    create_expense_lines,
    approve_expense,
    pay_expense,
)


@pytest.fixture
def sample_expense():
    return {
        "expense_id": "EXP-NEW-001",
        "vendor_id": "V-001",
        "bill_reference": "BILL-TEST-001",
        "category_account": "5101",
        "amount_excl_gst": 1000,
        "gst_amount": 180,
        "total_amount": 1180,
        "status": "SUBMITTED",
        "submitted_by": "EMP-0001",
        "approved_by": None,
        "ledger_entry_id": None,
        "payment_ledger_entry_id": None,
    }


def test_duplicate_expense_detected(sample_expense):
    existing = pd.DataFrame([
        {
            "expense_id": "EXP-OLD-001",
            "vendor_id": "V-001",
            "bill_reference": "BILL-TEST-001",
        }
    ])

    assert find_duplicate_expense(sample_expense, existing) is True


def test_different_vendor_is_not_duplicate(sample_expense):
    existing = pd.DataFrame([
        {
            "expense_id": "EXP-OLD-001",
            "vendor_id": "V-002",
            "bill_reference": "BILL-TEST-001",
        }
    ])

    assert find_duplicate_expense(sample_expense, existing) is False


def test_expense_lines_are_balanced(sample_expense):
    lines = create_expense_lines(sample_expense)

    debit = sum(line["debit"] for line in lines)
    credit = sum(line["credit"] for line in lines)

    assert debit == credit == 1180


def test_submitter_cannot_approve_own_expense(sample_expense):
    existing = pd.DataFrame(columns=[
        "expense_id", "vendor_id", "bill_reference"
    ])

    with pytest.raises(ValueError, match="Submitter cannot approve"):
        approve_expense(sample_expense, "EMP-0001", existing)


def test_expense_cannot_be_paid_before_approval(sample_expense):
    with pytest.raises(ValueError, match="Only approved expenses"):
        pay_expense(sample_expense, "2026-11-02")