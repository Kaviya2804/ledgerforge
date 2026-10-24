from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, select, update

from app.config import settings
from app.database import engine
from app.models import Department, Role, Employee, EmployeeAssignment


DATA_DIR = Path(settings.data_dir)

TABLES = [
    (Department, "departments.csv"),
    (Role, "roles.csv"),
    (Employee, "employees.csv"),
    (EmployeeAssignment, "employee_assignments.csv"),
]

COLUMN_RENAMES = {
    "departments.csv": {},
    "roles.csv": {},
    "employees.csv": {
        "employee_id": "emp_id",
        "first_name": "fname",
        "last_name": "lname",
        "date_of_birth": "dob",
        "highest_education": "highest_edu",
        "prior_experience_years": "prior_experience_year",
        "career_gap_months": "career_gap_month",
    },
    "employee_assignments.csv": {},
}

# Convert CSV Y/N values into Python Boolean values.
BOOLEAN_COLUMNS = {
    "roles.csv": ["overtime_eligible"],
    "employees.csv": ["pf_applicable", "esi_applicable"],
}

DATE_ONLY_COLUMNS = {
    "employees.csv": [
        "dob",
        "hire_date",
        "exit_date",
        "resignation_date",
    ],
    "employee_assignments.csv": [
        "effective_from",
        "effective_to",
    ],
}

DATETIME_COLUMNS = {
    "employees.csv": ["created_at"],
}


def clean_value(value):
    """Convert pandas values into database-compatible Python values."""
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, "item"):
        return value.item()

    return value


def load_data():
    dataframes = {}

    # Step 1: Read and validate all CSV files.
    for model, filename in TABLES:
        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {path}"
            )

        df = pd.read_csv(path)

        # Rename CSV columns to match the database model.
        df = df.rename(
            columns=COLUMN_RENAMES.get(filename, {})
        )

        # Convert Y/N values into True/False.
        for column in BOOLEAN_COLUMNS.get(filename, []):
            df[column] = df[column].map(
                lambda value: (
                    None
                    if pd.isna(value)
                    else str(value).strip().upper()
                    in ("Y", "YES", "TRUE", "1")
                )
            )

        # Validate column names.
        model_columns = set(model.__table__.columns.keys())
        csv_columns = set(df.columns)

        if csv_columns != model_columns:
            raise ValueError(
                f"Column mismatch in {filename}\n"
                f"Missing: {model_columns - csv_columns}\n"
                f"Unexpected: {csv_columns - model_columns}"
            )

        # Convert date-only columns.
        for column in DATE_ONLY_COLUMNS.get(filename, []):
            df[column] = pd.to_datetime(
                df[column],
                errors="raise",
            ).map(
                lambda value: (
                    value.date()
                    if pd.notna(value)
                    else None
                )
            )

        # Convert datetime columns.
        for column in DATETIME_COLUMNS.get(filename, []):
            df[column] = pd.to_datetime(
                df[column],
                errors="raise",
            ).map(
                lambda value: (
                    value.to_pydatetime()
                    if pd.notna(value)
                    else None
                )
            )

        # Replace missing values with None.
        df = df.astype(object).where(
            pd.notna(df),
            None,
        )

        dataframes[model] = df

    # Keep manager IDs for the second pass.
    manager_records = dataframes[Employee][
        ["emp_id", "manager_id"]
    ].to_dict(orient="records")

    # Step 2: Clear and reload everything in one transaction.
    with engine.begin() as connection:

        # Delete child tables before parent tables.
        for model, _ in reversed(TABLES):
            connection.execute(
                delete(model.__table__)
            )

        # Insert departments and roles first.
        for model in [Department, Role]:
            records = [
                {
                    key: clean_value(value)
                    for key, value in row.items()
                }
                for row in dataframes[model].to_dict(
                    orient="records"
                )
            ]

            if records:
                connection.execute(
                    model.__table__.insert(),
                    records,
                )

        # Insert employees without manager IDs first.
        employee_records = []

        for row in dataframes[Employee].to_dict(
            orient="records"
        ):
            record = {
                key: clean_value(value)
                for key, value in row.items()
            }

            record["manager_id"] = None
            employee_records.append(record)

        if employee_records:
            connection.execute(
                Employee.__table__.insert(),
                employee_records,
            )

        # Update manager IDs after all employees exist.
        for record in manager_records:
            manager_id = clean_value(
                record["manager_id"]
            )

            if manager_id is not None:
                connection.execute(
                    update(Employee.__table__)
                    .where(
                        Employee.__table__.c.emp_id
                        == clean_value(record["emp_id"])
                    )
                    .values(manager_id=manager_id)
                )

        # Insert employee assignments last.
        assignment_records = [
            {
                key: clean_value(value)
                for key, value in row.items()
            }
            for row in dataframes[EmployeeAssignment].to_dict(
                orient="records"
            )
        ]

        if assignment_records:
            connection.execute(
                EmployeeAssignment.__table__.insert(),
                assignment_records,
            )

        # Step 3: Verify row counts before committing.
        print("\nData Load Count Report")
        print("-" * 65)

        print(
            f"{'Table':25} "
            f"{'CSV Rows':>12} "
            f"{'DB Rows':>12} "
            f"{'Status':>10}"
        )

        for model, filename in TABLES:
            csv_count = len(dataframes[model])

            db_count = connection.execute(
                select(func.count()).select_from(
                    model.__table__
                )
            ).scalar_one()

            status = (
                "PASS"
                if csv_count == db_count
                else "FAIL"
            )

            print(
                f"{model.__tablename__:25} "
                f"{csv_count:>12} "
                f"{db_count:>12} "
                f"{status:>10}"
            )

            if status == "FAIL":
                raise ValueError(
                    f"Count mismatch for {model.__tablename__}"
                )

    print("\nData loading completed successfully.")


if __name__ == "__main__":
    load_data()