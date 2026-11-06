from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import csv


TWO_PLACES = Decimal("0.01")


def money(value) -> Decimal:
    """Convert a value into a two-decimal Decimal amount."""
    return Decimal(str(value or 0)).quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP,
    )
def load_statutory_rates(file_path: str) -> dict[str, Decimal]:
    """Load statutory rates from CSV."""

    import csv

    with open(file_path, newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)

        return {
            row["parameter"]: Decimal(row["value"])
            for row in rows
        }

def get_active_salary_components(
    salary_rows,
    employee_id,
    period_start,
    period_end
):
    """Get salary components active during the payroll period."""

    period_start = date.fromisoformat(str(period_start))
    period_end = date.fromisoformat(str(period_end))

    active_rows = []

    for row in salary_rows:
        if row["employee_id"] != employee_id:
            continue

        effective_from = date.fromisoformat(row["effective_from"])

        effective_to = (
            date.fromisoformat(row["effective_to"])
            if row["effective_to"]
            else None
        )

        overlaps = (
            effective_from <= period_end
            and (effective_to is None or effective_to >= period_start)
        )

        if overlaps:
            active_rows.append(row)

    revision_ids = {row["revision_id"] for row in active_rows}

    if len(revision_ids) != 1:
        raise ValueError(
            f"Expected one salary revision for {employee_id}, "
            f"found {len(revision_ids)}"
        )

    components = {}

    for row in active_rows:
        components[row["component_id"]] = money(row["monthly_amount"])

    return components
def calculate_monthly_fixed_gross(
    salary_components: dict[str, Decimal],
) -> Decimal:
    """Calculate total monthly fixed gross from salary components."""

    return money(sum(salary_components.values(), Decimal("0")))
def calculate_earned_components(
    salary_components: dict[str, Decimal],
    lop_days: Decimal,
    calendar_days: int,
) -> dict[str, Decimal]:
    """Calculate each salary component after LOP deduction."""

    earned_components = {}

    for component_id, amount in salary_components.items():
        earned_components[component_id] = calculate_lop(
            amount,
            lop_days,
            calendar_days,
        )

    return earned_components
def calculate_earned_fixed_pay(
    monthly_fixed_gross,
    lop_days,
    calendar_days
):
    """Calculate earned fixed salary after loss of pay."""

    monthly_gross = Decimal(str(monthly_fixed_gross))
    lop = Decimal(str(lop_days))
    days = Decimal(str(calendar_days))

    if days <= 0:
        raise ValueError("Calendar days must be greater than zero")

    if lop < 0 or lop > days:
        raise ValueError("Invalid LOP days")

    payable_days = days - lop

    earned_pay = monthly_gross * payable_days / days

    return money(earned_pay)
def calculate_gross_pay(
    earned_fixed_pay: Decimal,
    overtime_pay: Decimal,
    variable_pay: Decimal,
) -> Decimal:
    """Calculate total gross pay."""

    return money(
        Decimal(str(earned_fixed_pay))
        + Decimal(str(overtime_pay))
        + Decimal(str(variable_pay))
    )
def calculate_total_deductions(
    pf_employee: Decimal,
    esi_employee: Decimal,
    professional_tax: Decimal,
    tds: Decimal,
    other_deductions: Decimal,
) -> Decimal:
    """Calculate total employee deductions."""

    return money(
        pf_employee
        + esi_employee
        + professional_tax
        + tds
        + other_deductions
    )
def calculate_net_pay(
    gross_pay: Decimal,
    total_deductions: Decimal,
) -> Decimal:
    """Calculate employee net pay."""

    return money(
        Decimal(str(gross_pay))
        - Decimal(str(total_deductions))
    )
def calculate_lop(
    monthly_fixed_gross: Decimal,
    lop_days: Decimal,
    calendar_days: int,
) -> Decimal:
    """Calculate earned fixed pay after Loss of Pay."""

    if calendar_days <= 0:
        raise ValueError("Calendar days must be greater than zero.")

    payable_days = Decimal(calendar_days) - Decimal(str(lop_days))

    if payable_days < 0:
        raise ValueError("LOP days cannot exceed calendar days.")

    earned_fixed_pay = (
        Decimal(str(monthly_fixed_gross))
        * payable_days
        / Decimal(calendar_days)
    )

    return money(earned_fixed_pay)

def calculate_overtime(monthly_fixed_gross, overtime_hours, rates):
    """Calculate overtime pay using statutory rates."""

    cap = rates["OT_MONTHLY_CAP_HOURS"]
    multiplier = rates["OT_MULTIPLIER"]
    working_hours = rates["WORKING_HOURS_PER_MONTH"]

    paid_hours = min(Decimal(str(overtime_hours)), cap)

    hourly_rate = Decimal(str(monthly_fixed_gross)) / working_hours

    overtime_pay = hourly_rate * paid_hours * multiplier

    return paid_hours, money(overtime_pay)

def get_employee_eligibility(
    employee_row: dict,
) -> tuple[bool, bool]:
    """Return PF and ESI eligibility for an employee."""

    pf_applicable = employee_row["pf_applicable"] == "Y"
    esi_applicable = employee_row["esi_applicable"] == "Y"

    return pf_applicable, esi_applicable
def calculate_attendance_totals(
    attendance_rows,
    employee_id,
    period_start,
    period_end
):
    """Calculate LOP days and overtime hours for an employee."""

    period_start = date.fromisoformat(str(period_start))
    period_end = date.fromisoformat(str(period_end))

    lop_days = Decimal("0")
    overtime_hours = Decimal("0")

    for row in attendance_rows:

        if row["employee_id"] != employee_id:
            continue

        attendance_date = date.fromisoformat(
            row["attendance_date"]
        )

        if not period_start <= attendance_date <= period_end:
            continue

        status = row["status"]

        # Count loss of pay
        if status in ("ABSENT_LOP", "UNPAID_LEAVE"):
            lop_days += Decimal("1")
            continue

        elif status == "HALF_DAY_UNPAID":
            lop_days += Decimal("0.5")
            continue

        # Ignore incomplete attendance records
        if row.get("check_in") and not row.get("check_out"):
            continue

        # Add overtime only from complete attendance records
        overtime_hours += Decimal(
            row["overtime_hours"] or "0"
        )

    return money(lop_days), money(overtime_hours)
def calculate_pf(basic_salary, pf_applicable, rates):
    """Calculate employee and employer PF contributions."""

    if not pf_applicable:
        return money(0), money(0)

    wage_ceiling = rates["PF_WAGE_CEILING"]
    employee_rate = rates["PF_EMPLOYEE_RATE"] / Decimal("100")
    employer_rate = rates["PF_EMPLOYER_RATE"] / Decimal("100")

    pf_wage = min(Decimal(str(basic_salary)), wage_ceiling)

    employee_pf = pf_wage * employee_rate
    employer_pf = pf_wage * employer_rate

    return money(employee_pf), money(employer_pf)

def calculate_esi(gross_pay, monthly_fixed_gross, esi_applicable, rates):
    esi_limit = rates["ESI_WAGE_LIMIT"]

    if Decimal(str(monthly_fixed_gross)) > esi_limit:
        return money(0), money(0)

    employee_rate = rates["ESI_EMPLOYEE_RATE"] / Decimal("100")
    employer_rate = rates["ESI_EMPLOYER_RATE"] / Decimal("100")

    gross = Decimal(str(gross_pay))
    return money(gross * employee_rate), money(gross * employer_rate)
def calculate_pt(monthly_fixed_gross, rates):
    threshold = rates["PT_GROSS_THRESHOLD"]
    pt_amount = rates["PT_MONTHLY"]

    if Decimal(str(monthly_fixed_gross)) >= threshold:
        return money(pt_amount)

    return money(0)
def calculate_annual_tax(taxable_income, tax_slabs):
    """Calculate annual tax using progressive tax slabs."""

    income = Decimal(str(taxable_income))
    total_tax = Decimal("0")

    for slab in tax_slabs:
        lower = slab["income_from"]
        upper = slab["income_to"]
        rate = slab["rate"]

        if income <= lower:
            continue

        taxable_amount = (
            income - lower
            if upper is None
            else min(income, upper) - lower
        )

        total_tax += taxable_amount * rate

    return money(total_tax)


def calculate_tax_after_rebate(taxable_income, tax_slabs, tax_parameters):
    """Apply rebate threshold and marginal relief."""

    income = Decimal(str(taxable_income))
    rebate_threshold = tax_parameters["rebate_threshold_taxable"]

    if income <= rebate_threshold:
        return money(0)

    annual_tax = calculate_annual_tax(income, tax_slabs)

    marginal_relief_limit = income - rebate_threshold

    return money(min(annual_tax, marginal_relief_limit))

def calculate_tax_with_cess(taxable_income, tax_slabs, tax_parameters):
    """Calculate annual tax including cess."""

    tax = calculate_tax_after_rebate(
        taxable_income,
        tax_slabs,
        tax_parameters
    )

    cess_rate = (
        tax_parameters["health_education_cess_percent"]
        / Decimal("100")
    )

    return money(tax + (tax * cess_rate))

def calculate_monthly_tds(
    projected_annual_income,
    tax_parameters,
    tax_slabs
):
    """Calculate monthly TDS from projected annual income."""

    taxable_income = calculate_projected_taxable_income(
        projected_annual_income,
        tax_parameters
    )

    annual_tax = calculate_tax_with_cess(
        taxable_income,
        tax_slabs,
        tax_parameters
    )

    return money(annual_tax / Decimal("12"))

def calculate_projected_taxable_income(projected_annual_income, tax_parameters):
    """Calculate annual taxable income after standard deduction."""

    standard_deduction = tax_parameters["standard_deduction"]

    taxable_income = (
        Decimal(str(projected_annual_income)) - standard_deduction
    )

    return max(Decimal("0"), taxable_income)

def calculate_marginal_tax_on_variable_pay(
    projected_annual_income,
    variable_pay,
    tax_parameters,
    tax_slabs
):
    """Calculate additional annual tax caused by variable pay."""

    income = Decimal(str(projected_annual_income))
    bonus = Decimal(str(variable_pay))

    tax_without_bonus = calculate_monthly_tds(
        income, tax_parameters, tax_slabs
    )

    tax_with_bonus = calculate_monthly_tds(
        income + bonus, tax_parameters, tax_slabs
    )

    return money((tax_with_bonus - tax_without_bonus)*Decimal("12"))
def load_tax_parameters(file_path: str) -> dict[str, Decimal]:
    """Load tax parameters from CSV."""

    import csv

    with open(file_path, newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)

        return {
            row["parameter"]: Decimal(row["value"])
            for row in rows
        }
def load_tax_slabs(file_path: str, financial_year: str) -> list[dict]:
    """Load NEW regime tax slabs for the selected financial year."""

    import csv

    slabs = []

    with open(file_path, newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)

        for row in rows:
            if (
                row["regime"] == "NEW"
                and row["financial_year"] == financial_year
            ):
                slabs.append({
                    "income_from": Decimal(row["income_from"]),
                    "income_to": (
                        Decimal(row["income_to"])
                        if row["income_to"]
                        else None
                    ),
                    "rate": Decimal(row["rate_percent"]) / Decimal("100"),
                })

    return slabs
def load_csv_rows(file_path: str) -> list[dict]:
    """Load CSV records as dictionaries."""

    import csv

    with open(file_path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
def get_employee_by_id(employee_rows, employee_id):
    """Find an employee record by employee ID."""

    for row in employee_rows:
        if row["employee_id"] == employee_id:
            return row

    raise ValueError(f"Employee not found: {employee_id}")
def get_financial_year(period_start):
    """Return financial year in FY2025-26 format."""

    if isinstance(period_start, str):
        period_start = date.fromisoformat(period_start)

    if period_start.month >= 4:
        start_year = period_start.year
    else:
        start_year = period_start.year - 1

    end_year = start_year + 1

    return f"FY{start_year}-{str(end_year)[-2:]}"
def get_role_by_id(role_rows, role_id):
    """Find a role record by role ID."""

    for row in role_rows:
        if row["role_id"] == role_id:
            return row

    raise ValueError(f"Role not found: {role_id}")
def get_active_assignment(
    assignment_rows,
    employee_id,
    period_start,
    period_end,
    employment_end=None
):
    """Find the assignment active on the employee's last working day."""

    end = date.fromisoformat(str(period_end))

    if employment_end:
        end = min(
            end,
            date.fromisoformat(str(employment_end))
        )

    active_assignments = []

    for row in assignment_rows:
        if row["employee_id"] != employee_id:
            continue

        effective_from = date.fromisoformat(row["effective_from"])

        effective_to = (
            date.fromisoformat(row["effective_to"])
            if row["effective_to"]
            else None
        )

        if (
            effective_from <= end
            and (effective_to is None or effective_to >= end)
        ):
            active_assignments.append(row)

    if len(active_assignments) != 1:
        raise ValueError(
            f"Expected one assignment active on {end} for {employee_id}, "
            f"found {len(active_assignments)}"
        )

    return active_assignments[0]
def calculate_employee_month(
    employee_id,
    period_start,
    period_end,
    employees,
    assignments,
    roles,
    salary_rows,
    attendance_rows,
    statutory_rates,
    tax_parameters,
    tax_slabs,
    variable_pay=0,
    other_deductions=0
):
    """Calculate one employee's payroll for one month."""

    # 1. Get employee details
    employee = get_employee_by_id(employees, employee_id)

    # 2. Get active assignment and role
    assignment = get_active_assignment(
        assignments, employee_id, period_start, period_end, employee["exit_date"]
    )
    role = get_role_by_id(roles, assignment["role_id"])

    # 3. Get salary components
    salary_components = get_active_salary_components(
        salary_rows, employee_id, period_start, period_end
    )

    monthly_fixed_gross = calculate_monthly_fixed_gross(
        salary_components
    )

    # 4. Calculate attendance
    lop_days, overtime_hours = calculate_attendance_totals(
        attendance_rows,
        employee_id,
        period_start,
        period_end
    )

    start = date.fromisoformat(str(period_start))
    end = date.fromisoformat(str(period_end))

    calendar_days = (end - start).days + 1

    if calendar_days <= 0:
        raise ValueError("Invalid payroll period")

    hire_date = date.fromisoformat(employee["hire_date"])

    exit_date = (
        date.fromisoformat(employee["exit_date"])
        if employee["exit_date"]
        else None
    )

    employment_start = max(start, hire_date)
    employment_end = min(end, exit_date) if exit_date else end

    days_employed = max(
        0,
        (employment_end - employment_start).days + 1
    )

    # 5. Calculate earned fixed pay
    if days_employed == 0:
        earned_fixed_pay = money(0)
    else:
        employed_monthly_pay = money(
            monthly_fixed_gross
            * Decimal(days_employed)
            / Decimal(calendar_days)
        )

        earned_fixed_pay = calculate_earned_fixed_pay(
            employed_monthly_pay,
            lop_days,
            days_employed
        )

    # 6. Calculate overtime
    if role["overtime_eligible"] == "Y" and days_employed > 0:
        overtime_hours_paid, overtime_pay = calculate_overtime(
            monthly_fixed_gross,
            overtime_hours,
            statutory_rates
        )
    else:
        overtime_hours_paid = money(0)
        overtime_pay = money(0)

    # 7. Calculate gross pay
    gross_pay = calculate_gross_pay(
        earned_fixed_pay,
        overtime_pay,
        variable_pay
    )

    # 8. Calculate PF and ESI
    payable_days = Decimal(days_employed) - Decimal(str(lop_days))

    earned_basic = money(
        salary_components.get("BASIC", money(0))
        * payable_days
        / Decimal(calendar_days)
    )

    pf_employee, pf_employer = calculate_pf(
        earned_basic,
        employee["pf_applicable"] == "Y",
        statutory_rates
    )

    esi_employee, esi_employer = calculate_esi(
        gross_pay,
        monthly_fixed_gross,
        employee["esi_applicable"],
        statutory_rates
    )

    # 9. Professional tax
    professional_tax = calculate_pt(
        monthly_fixed_gross,
        statutory_rates
    )

    # 10. Calculate TDS
    annual_projected_income = (
        monthly_fixed_gross * Decimal("12")
    )

    full_month_tds = calculate_monthly_tds(
        annual_projected_income,
        tax_parameters,
        tax_slabs
    )

    variable_pay_amount = money(variable_pay)

    marginal_tax = calculate_marginal_tax_on_variable_pay(
        annual_projected_income,
        variable_pay_amount,
        tax_parameters,
        tax_slabs
    )

    # Prorate TDS according to payable days.
    if payable_days <= 0:
        tds = money(0)
    else:
        tds_before_proration = full_month_tds + marginal_tax

        tds = money(
            tds_before_proration
            * payable_days
            / Decimal(calendar_days)
        )
    # 11. Calculate total deductions and net pay
    total_deductions = calculate_total_deductions(
        pf_employee,
        esi_employee,
        professional_tax,
        tds,
        other_deductions
    )

    net_pay = calculate_net_pay(
        gross_pay,
        total_deductions
    )

    # 12. Return payroll details
    return {
        "employee_id": employee_id,
        "monthly_fixed_gross": monthly_fixed_gross,
        "days_employed": days_employed,
        "lop_days": lop_days,
        "earned_fixed_pay": earned_fixed_pay,
        "overtime_hours_paid": overtime_hours_paid,
        "overtime_pay": overtime_pay,
        "variable_pay": variable_pay_amount,
        "gross_pay": gross_pay,
        "pf_employee": pf_employee,
        "pf_employer": pf_employer,
        "esi_employee": esi_employee,
        "esi_employer": esi_employer,
        "professional_tax": professional_tax,
        "tds": tds,
        "other_deductions": money(other_deductions),
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "employer_cost": money(
            gross_pay + pf_employer + esi_employer
        )
    }