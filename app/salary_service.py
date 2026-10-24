from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import (
    Employee,
    Role,
    SalaryComponent,
    SalaryRevision,
    SalaryStructure,
)


def _generate_id(prefix: str) -> str:
    """Generate a unique ID within the 20-character database limit."""
    return f"{prefix}{uuid4().hex[:16]}"


def get_structure(
    db: Session,
    employee_id: str,
    target_date: date,
):
    """Return salary components active on the requested date."""
    return (
        db.query(SalaryStructure)
        .filter(
            SalaryStructure.employee_id == employee_id,
            SalaryStructure.effective_from <= target_date,
            (
                SalaryStructure.effective_to.is_(None)
                | (SalaryStructure.effective_to >= target_date)
            ),
        )
        .order_by(SalaryStructure.component_id)
        .all()
    )


def revise_salary(
    db: Session,
    employee_id: str,
    effective_date: date,
    new_annual_fixed: Decimal,
    revision_reason: str,
    role_id_after: str,
    approved_by: str | None = None,
):
    """Close the previous salary structure and create a new revision."""

    try:
        employee = db.get(Employee, employee_id)
        if employee is None:
            raise ValueError("Employee not found")

        if new_annual_fixed <= Decimal("0"):
            raise ValueError("Annual salary must be greater than zero")

        if not revision_reason or not revision_reason.strip():
            raise ValueError("Revision reason is required")

        role = db.get(Role, role_id_after)
        if role is None:
            raise ValueError("Role not found")

        existing_revision = (
            db.query(SalaryRevision)
            .filter(
                SalaryRevision.employee_id == employee_id,
                SalaryRevision.effective_from >= effective_date,
            )
            .first()
        )
        if existing_revision:
            raise ValueError(
                "A salary revision already exists on or after this date"
            )

        previous_date = effective_date - timedelta(days=1)

        old_structures = get_structure(
            db,
            employee_id,
            previous_date,
        )
        if not old_structures:
            raise ValueError(
                "No previous salary structure found before the revision date"
            )

        fixed_ids = {"BASIC", "HRA", "CONV", "MED", "SPECIAL"}

        previous_monthly = sum(
            (
                Decimal(str(item.monthly_amount))
                for item in old_structures
                if item.component_id in fixed_ids
            ),
            Decimal("0.00"),
        )
        previous_annual = previous_monthly * Decimal("12")

        components = (
            db.query(SalaryComponent)
            .filter(SalaryComponent.component_id.in_(fixed_ids))
            .all()
        )
        component_map = {
            component.component_id: component
            for component in components
        }

        missing = fixed_ids - set(component_map)
        if missing:
            raise ValueError(
                "Missing salary components: "
                + ", ".join(sorted(missing))
            )

        monthly_gross = (
            new_annual_fixed / Decimal("12")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        basic = (
            monthly_gross * Decimal("0.40")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        hra = (
            basic * Decimal("0.50")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        conveyance = (
            Decimal("1600.00")
            if monthly_gross >= Decimal("20000.00")
            else Decimal("800.00")
        )

        medical = (
            Decimal("1250.00")
            if monthly_gross >= Decimal("20000.00")
            else Decimal("0.00")
        )

        special = (
            monthly_gross - basic - hra - conveyance - medical
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if special < Decimal("0"):
            raise ValueError(
                "Calculated salary components exceed the monthly salary"
            )

        amounts = {
            "BASIC": basic,
            "HRA": hra,
            "CONV": conveyance,
            "MED": medical,
            "SPECIAL": special,
        }

        revision = SalaryRevision(
            revision_id=_generate_id("REV"),
            employee_id=employee_id,
            effective_from=effective_date,
            revision_reason=revision_reason.strip(),
            previous_annual_fixed=previous_annual,
            new_annual_fixed=new_annual_fixed,
            pct_change=(
                (
                    (new_annual_fixed - previous_annual)
                    / previous_annual
                    * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if previous_annual > 0
                else Decimal("0.00")
            ),
            role_id_after=role_id_after,
            approved_by=approved_by,
            created_at=datetime.now(),
        )

        db.add(revision)
        db.flush()

        for item in old_structures:
            item.effective_to = previous_date

        for component_id, amount in amounts.items():
            component = component_map[component_id]

            db.add(
                SalaryStructure(
                    structure_id=_generate_id("STR"),
                    employee_id=employee_id,
                    component_id=component_id,
                    component_name=component.component_name,
                    component_type=component.component_type,
                    monthly_amount=amount,
                    effective_from=effective_date,
                    effective_to=None,
                    revision_id=revision.revision_id,
                )
            )

        db.commit()
        db.refresh(revision)

        return revision

    except Exception:
        db.rollback()
        raise