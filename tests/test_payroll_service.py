from decimal import Decimal

from app.payroll_service import (calculate_attendance_totals, calculate_lop, calculate_overtime, calculate_pf, calculate_esi, calculate_pt,)


def test_payroll_attendance_ignores_missing_checkout_overtime():
    attendance_rows = [
        {
            "employee_id": "EMP-TEST-01",
            "attendance_date": "2025-04-02",
            "status": "PRESENT",
            "check_in": "09:00:00",
            "check_out": None,
            "overtime_hours": "2.00",
        },
        {
            "employee_id": "EMP-TEST-01",
            "attendance_date": "2025-04-03",
            "status": "PRESENT",
            "check_in": "09:00:00",
            "check_out": "18:00:00",
            "overtime_hours": "1.50",
        },
    ]

    lop_days, overtime_hours = calculate_attendance_totals(
        attendance_rows,
        "EMP-TEST-01",
        "2025-04-01",
        "2025-04-30",
    )


    assert lop_days == Decimal("0.00")
    assert overtime_hours == Decimal("1.50")
from app.payroll_service import calculate_lop


def test_calculate_lop():
    earned_pay = calculate_lop(
        Decimal("30000"),
        Decimal("2"),
        30,
    )

    assert earned_pay == Decimal("28000.00")
def test_calculate_overtime():
    rates = {
        "OT_MONTHLY_CAP_HOURS": Decimal("50"),
        "OT_MULTIPLIER": Decimal("2"),
        "WORKING_HOURS_PER_MONTH": Decimal("208"),
    }

    paid_hours, overtime_pay = calculate_overtime(
        Decimal("41600"),
        Decimal("10"),
        rates,
    )

    assert paid_hours == Decimal("10")
    assert overtime_pay == Decimal("4000.00")
def test_calculate_pf():
    rates = {
        "PF_WAGE_CEILING": Decimal("15000"),
        "PF_EMPLOYEE_RATE": Decimal("12"),
        "PF_EMPLOYER_RATE": Decimal("12"),
    }

    employee_pf, employer_pf = calculate_pf(
        Decimal("20000"),
        True,
        rates,
    )

    assert employee_pf == Decimal("1800.00")
    assert employer_pf == Decimal("1800.00")
def test_calculate_esi():
    rates = {
        "ESI_WAGE_LIMIT": Decimal("21000"),
        "ESI_EMPLOYEE_RATE": Decimal("0.75"),
        "ESI_EMPLOYER_RATE": Decimal("3.25"),
    }

    employee_esi, employer_esi = calculate_esi(
        Decimal("20000"),
        Decimal("20000"),
        "Permanent",
        rates,
    )

    assert employee_esi == Decimal("150.00")
    assert employer_esi == Decimal("650.00")
def test_calculate_pt():
    rates = {
        "PT_GROSS_THRESHOLD": Decimal("25000"),
        "PT_MONTHLY": Decimal("200"),
    }

    assert calculate_pt(Decimal("30000"), rates) == Decimal("200.00")
    assert calculate_pt(Decimal("20000"), rates) == Decimal("0.00")
    assert calculate_pt(Decimal("25000"), rates) == Decimal("200.00")
