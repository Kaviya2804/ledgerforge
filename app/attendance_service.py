from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Attendance, Holiday


def monthly_summary(
    session: Session,
    employee_id: str,
    month: str,
) -> dict:
    """Return an employee's attendance summary for a month (YYYY-MM)."""

    # Validate month and calculate date range.
    try:
        year, month_number = map(int, month.split("-"))
        start_date = date(year, month_number, 1)

        if month_number == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month_number + 1, 1)

    except (ValueError, TypeError):
        raise ValueError(
            "Month must be in YYYY-MM format, e.g. 2025-04"
        )

    # Get holidays for the selected month.
    holidays = {
        row[0]
        for row in session.query(Holiday.holiday_date)
        .filter(
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date < end_date,
        )
        .all()
    }

    # Get employee attendance records for the selected month.
    records = (
        session.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date < end_date,
        )
        .all()
    )

    # Initialize summary.
    summary = {
        "employee_id": employee_id,
        "month": month,
        "present_days": 0,
        "wfh_days": 0,
        "absent_days": 0,
        "late_days": 0,
        "overtime_hours": Decimal("0.00"),
        "missing_checkout_days": 0,
    }

    for record in records:
        attendance_date = record.attendance_date

        # Skip weekends and holidays.
        if attendance_date.weekday() >= 5 or attendance_date in holidays:
            continue

        status = (record.status or "").strip().upper()

        # Count attendance status.
        if status == "PRESENT":
            summary["present_days"] += 1

        elif status in {"WFH", "WORK FROM HOME"}:
            summary["wfh_days"] += 1

        elif status in {
            "ABSENT",
            "ABSENT_LOP",
            "HALF_DAY_UNPAID",
            "UNPAID_LEAVE",
        }:
            summary["absent_days"] += 1

        # Identify missing checkout records.
        missing_checkout = (
            record.check_in is not None
            and record.check_out is None
        )

        if missing_checkout:
            summary["missing_checkout_days"] += 1

        # Count late attendance only on eligible working days.
        if (record.late_flag or "").strip().upper() == "Y":
            summary["late_days"] += 1

        # Do not count overtime when checkout is missing.
        if (
            not missing_checkout
            and record.overtime_hours is not None
        ):
            summary["overtime_hours"] += Decimal(
                str(record.overtime_hours)
            )

    # Format overtime to two decimal places.
    summary["overtime_hours"] = summary["overtime_hours"].quantize(
        Decimal("0.01")
    )

    return summary