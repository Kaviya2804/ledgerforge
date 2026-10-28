import pandas as pd
from pathlib import Path

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Department,
    Role,
    Employee,
    EmployeeAssignment,
    SalaryComponent,
    SalaryRevision,
    SalaryStructure,
    Attendance,
    LeaveType,
    LeaveRequest,
    LeaveBalance,
    Holiday,
)


def get_csv_path(filename: str) -> Path:
    """Return the path of a CSV file."""
    return Path(settings.data_dir) / filename


def prepare_dataframe(
    df: pd.DataFrame,
    filename: str,
) -> pd.DataFrame:
    """Prepare CSV values for SQLAlchemy models."""

    # Rename employee CSV columns to match the model.
    if filename == "employees.csv":
        df = df.rename(
            columns={
                "employee_id": "emp_id",
                "first_name": "fname",
                "last_name": "lname",
                "date_of_birth": "dob",
                "highest_education": "highest_edu",
                "prior_experience_years": "prior_experience_year",
                "career_gap_months": "career_gap_month",
            }
        )

    # Convert Y/N values to Boolean.
    boolean_columns = {
        "roles.csv": ["overtime_eligible"],
        "employees.csv": ["pf_applicable", "esi_applicable"],
        "leave_types.csv": [
            "prorated_for_joiners",
            "carry_forward_allowed",
        ],
        "holidays.csv": ["falls_on_weekend"],
    }

    for column in boolean_columns.get(filename, []):
        if column in df.columns:
            df[column] = df[column].map(
                {
                    "Y": True,
                    "N": False,
                    "y": True,
                    "n": False,
                }
            )

    # Convert date columns.
    date_columns = {
        "employees.csv": [
            "dob",
            "hire_date",
            "exit_date",
            "resignation_date",
            "created_at",
        ],
        "employee_assignments.csv": [
            "effective_from",
            "effective_to",
        ],
        "salary_revisions.csv": [
            "effective_from",
            "created_at",
        ],
        "salary_structures.csv": [
            "effective_from",
            "effective_to",
        ],
        "attendance.csv": ["attendance_date"],
        "leave_requests.csv": [
            "start_date",
            "end_date",
            "applied_on",
            "decided_on",
        ],
        "leave_balances.csv": ["as_of_date"],
        "holidays.csv": ["holiday_date"],
    }

    for column in date_columns.get(filename, []):
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="raise",
            )

            if column != "created_at":
                df[column] = df[column].dt.date

    # Convert missing values to Python None.
    df = df.astype(object).where(pd.notna(df), None)

    return df


def read_csv(filename: str) -> pd.DataFrame:
    """Read and prepare a complete CSV file."""

    file_path = get_csv_path(filename)

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path.resolve()}"
        )

    df = pd.read_csv(file_path)

    return prepare_dataframe(df, filename)


def load_csv_to_table(
    session,
    filename: str,
    model,
    table_name: str,
) -> None:
    """Load CSV data into the corresponding database table."""

    file_path = get_csv_path(filename)

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path.resolve()}"
        )

    # Attendance contains many rows, so process it in chunks.
    if filename == "attendance.csv":
        from sqlalchemy import insert

        chunk_size = 10000
        total_loaded = 0

        for chunk in pd.read_csv(
            file_path,
            chunksize=chunk_size,
        ):
            chunk = prepare_dataframe(chunk, filename)
            records = chunk.to_dict(orient="records")

            if records:
                session.execute(
                    insert(model),
                    records,
                )
                session.flush()

            total_loaded += len(records)

            print(
                f"{table_name}: Processed {total_loaded} rows",
                flush=True,
            )

        print(
            f"{table_name}: Finished processing "
            f"{total_loaded} rows",
            flush=True,
        )

        return
    # Other CSV files use merge to support existing records.
    df = read_csv(filename)
    records = df.to_dict(orient="records")

    print(
        f"{table_name}: Reading {len(records)} rows",
        flush=True,
    )

    for record in records:
        session.merge(model(**record))

    session.flush()

    print(
        f"{table_name}: Loaded {len(records)} rows",
        flush=True,
    )


# Parent tables must be loaded before dependent tables.
TABLES = [
    ("departments.csv", Department, "departments"),
    ("roles.csv", Role, "roles"),
    ("employees.csv", Employee, "employees"),
    (
        "employee_assignments.csv",
        EmployeeAssignment,
        "employee_assignments",
    ),
    (
        "salary_components.csv",
        SalaryComponent,
        "salary_components",
    ),
    (
        "salary_revisions.csv",
        SalaryRevision,
        "salary_revisions",
    ),
    (
        "salary_structures.csv",
        SalaryStructure,
        "salary_structures",
    ),
    ("leave_types.csv", LeaveType, "leave_types"),
    ("holidays.csv", Holiday, "holidays"),
    ("attendance.csv", Attendance, "attendance"),
    ("leave_requests.csv", LeaveRequest, "leave_requests"),
    ("leave_balances.csv", LeaveBalance, "leave_balances"),
]


def load_company_data() -> None:
    """Load all company data in a single transaction."""

    with SessionLocal() as session:
        try:
            for filename, model, table_name in TABLES:
                load_csv_to_table(
                    session,
                    filename,
                    model,
                    table_name,
                )

            session.commit()

            print(
                "\nAll company data loaded successfully!",
                flush=True,
            )

        except Exception:
            session.rollback()

            print(
                "\nLoading failed. Database changes "
                "were rolled back.",
                flush=True,
            )
            raise


if __name__ == "__main__":
    load_company_data()