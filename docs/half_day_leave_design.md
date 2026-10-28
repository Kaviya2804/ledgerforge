Half-Day Leave Design

1. Objective

Support half-day leave requests in the Aura Workforce leave management system.

2. Business Rules

- Employees can apply for a half-day leave.
- A half-day leave is counted as 0.5 leave day.
- The leave date must be a valid working day.
- Weekends and holidays are excluded from leave calculations.
- The employee must have sufficient leave balance for the requested leave.
- The leave request must be approved by an authorized approver before the leave balance is reduced.
- Rejected requests must not reduce the leave balance.

3. Database Design

The "leave_requests" table can include a "day_part" field.

Possible values:

- "FULL_DAY"
- "FIRST_HALF"
- "SECOND_HALF"

For a half-day request, the "days" field stores "0.5".

4. Leave Balance Calculation

Example:

An employee has 10 days of Casual Leave.

After approval of one half-day leave:

Remaining balance = 10 - 0.5 = 9.5 days.

5. Validation

- The start date and end date must be valid.
- A half-day request must cover only one date.
- Duplicate or overlapping leave requests must be prevented.
- Insufficient leave balance must result in validation failure.

6. Implementation Status

This document describes the proposed design only. Half-day leave functionality has not yet been implemented.