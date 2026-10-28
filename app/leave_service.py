from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    Employee,
    Holiday,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)


def calculate_leave_days(
    session: Session,
    start_date: date,
    end_date: date,
) -> Decimal:
    """Calculate leave days excluding weekends and company holidays."""

    if end_date < start_date:
        raise ValueError("End date cannot be before start date.")

    holidays = {
        row[0]
        for row in session.query(Holiday.holiday_date)
        .filter(
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date <= end_date,
        )
        .all()
    }

    total_days = 0
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() < 5 and current_date not in holidays:
            total_days += 1

        current_date += timedelta(days=1)

    return Decimal(str(total_days))


def get_leave_balance(
    session: Session,
    employee_id: str,
    leave_type_code: str,
) -> Decimal:
    """Return the latest balance for CL, SL or EL."""

    code = leave_type_code.strip().upper()

    balance_fields = {
        "CL": "cl_balance",
        "SL": "sl_balance",
        "EL": "el_balance",
    }

    if code not in balance_fields:
        raise ValueError(
            f"Balance lookup is not supported for leave type: {code}"
        )

    balance_record = (
        session.query(LeaveBalance)
        .filter(LeaveBalance.employee_id == employee_id)
        .order_by(LeaveBalance.as_of_date.desc())
        .first()
    )

    if balance_record is None:
        raise ValueError(
            f"No leave balance found for employee {employee_id}."
        )

    balance_value = getattr(
        balance_record,
        balance_fields[code],
    )

    if balance_value is None:
        raise ValueError(
            f"Leave balance is missing for {employee_id} ({code})."
        )

    return Decimal(str(balance_value))


def validate_leave_application(
    session: Session,
    employee_id: str,
    leave_type_code: str,
    start_date: date,
    end_date: date,
) -> dict:
    """Validate leave type, dates and available balance."""

    code = leave_type_code.strip().upper()

    if end_date < start_date:
        raise ValueError("End date cannot be before start date.")

    leave_type = (
        session.query(LeaveType)
        .filter(LeaveType.leave_type_code == code)
        .first()
    )

    if leave_type is None:
        raise ValueError(f"Invalid leave type: {code}")

    leave_days = calculate_leave_days(
        session,
        start_date,
        end_date,
    )

    if leave_days <= 0:
        raise ValueError(
            "The selected date range contains no eligible working days."
        )

    if code in {"CL", "SL", "EL"}:
        available_balance = get_leave_balance(
            session,
            employee_id,
            code,
        )

        if leave_days > available_balance:
            raise ValueError(
                f"Insufficient {code} balance. "
                f"Available: {available_balance} days; "
                f"Requested: {leave_days} days."
            )

    elif code == "LOP":
        available_balance = None

    else:
        # ML and BL require separate eligibility rules.
        available_balance = None

    return {
        "employee_id": employee_id,
        "leave_type_code": code,
        "start_date": start_date,
        "end_date": end_date,
        "days": leave_days,
        "available_balance": available_balance,
        "status": "Pending",
    }


def apply_leave(
    session: Session,
    employee_id: str,
    leave_type_code: str,
    start_date: date,
    end_date: date,
    reason: str | None = None,
) -> LeaveRequest:
    """Validate and create a new Pending leave request."""

    employee = (
        session.query(Employee)
        .filter(Employee.emp_id == employee_id)
        .first()
    )

    if employee is None:
        raise ValueError(f"Employee not found: {employee_id}")

    validation = validate_leave_application(
        session=session,
        employee_id=employee_id,
        leave_type_code=leave_type_code,
        start_date=start_date,
        end_date=end_date,
    )

    overlapping_request = (
        session.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(["Pending", "Approved"]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .first()
    )

    if overlapping_request is not None:
        raise ValueError(
            "An existing pending or approved leave request "
            "overlaps with these dates."
        )

    existing_ids = session.query(
        LeaveRequest.leave_request_id
    ).all()

    highest_number = 0

    for (request_id,) in existing_ids:
        if request_id and request_id.startswith("LR-"):
            suffix = request_id[3:]

            if suffix.isdigit():
                highest_number = max(
                    highest_number,
                    int(suffix),
                )

    new_request_id = f"LR-{highest_number + 1:06d}"

    request = LeaveRequest(
        leave_request_id=new_request_id,
        employee_id=employee_id,
        leave_type_code=validation["leave_type_code"],
        start_date=start_date,
        end_date=end_date,
        days=validation["days"],
        reason=reason,
        status="Pending",
        applied_on=date.today(),
        approver_id=None,
        decided_on=None,
    )

    try:
        session.add(request)
        session.commit()
        session.refresh(request)

    except Exception:
        session.rollback()
        raise

    return request


def approve_leave(
    session: Session,
    leave_request_id: str,
    approver_id: str,
) -> LeaveRequest:
    """Approve a pending request and deduct its paid leave balance."""

    request = (
        session.query(LeaveRequest)
        .filter(
            LeaveRequest.leave_request_id == leave_request_id
        )
        .first()
    )

    if request is None:
        raise ValueError(
            f"Leave request not found: {leave_request_id}"
        )

    if request.status != "Pending":
        raise ValueError(
            "Only pending leave requests can be approved."
        )

    code = request.leave_type_code.upper()

    balance_fields = {
        "CL": ("cl_balance", "cl_used"),
        "SL": ("sl_balance", "sl_used"),
        "EL": ("el_balance", "el_used_fy"),
    }

    try:
        if code in balance_fields:
            balance_record = (
                session.query(LeaveBalance)
                .filter(
                    LeaveBalance.employee_id == request.employee_id
                )
                .order_by(LeaveBalance.as_of_date.desc())
                .first()
            )

            if balance_record is None:
                raise ValueError(
                    f"No leave balance found for "
                    f"{request.employee_id}."
                )

            balance_field, used_field = balance_fields[code]

            current_balance = getattr(
                balance_record,
                balance_field,
            )

            current_used = getattr(
                balance_record,
                used_field,
            )

            if current_balance is None:
                raise ValueError(
                    f"Missing {code} balance for "
                    f"{request.employee_id}."
                )

            current_balance = Decimal(str(current_balance))
            current_used = Decimal(str(current_used or 0))
            requested_days = Decimal(str(request.days))

            if requested_days > current_balance:
                raise ValueError(
                    f"Insufficient {code} balance. "
                    f"Available: {current_balance}; "
                    f"Requested: {requested_days}."
                )

            setattr(
                balance_record,
                balance_field,
                current_balance - requested_days,
            )

            setattr(
                balance_record,
                used_field,
                current_used + requested_days,
            )

        request.status = "Approved"
        request.approver_id = approver_id
        request.decided_on = date.today()

        session.commit()
        session.refresh(request)

    except Exception:
        session.rollback()
        raise

    return request


def reject_leave(
    session: Session,
    leave_request_id: str,
    approver_id: str,
) -> LeaveRequest:
    """Reject a pending request without deducting leave balance."""

    request = (
        session.query(LeaveRequest)
        .filter(
            LeaveRequest.leave_request_id == leave_request_id
        )
        .first()
    )

    if request is None:
        raise ValueError(
            f"Leave request not found: {leave_request_id}"
        )

    if request.status != "Pending":
        raise ValueError(
            "Only pending leave requests can be rejected."
        )

    try:
        request.status = "Rejected"
        request.approver_id = approver_id
        request.decided_on = date.today()

        session.commit()
        session.refresh(request)

    except Exception:
        session.rollback()
        raise

    return request