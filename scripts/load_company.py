import pandas as pd
from pathlib import Path

from app.database import SessionLocal
from app.models import (
    Department,
    Role,
    Employee,
    EmployeeAssignment,
    SalaryComponent,
    SalaryRevision,
    SalaryStructure,
)
from app.config import settings


def get_csv_path(filename: str) -> Path:
    return Path(settings.data_dir) / filename


def read_csv(filename: str) -> pd.DataFrame:
    file_path = get_csv_path(filename)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    df = pd.read_csv(file_path)

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
    }

    for column in boolean_columns.get(filename, []):
        df[column] = (
            df[column]
            .map({"Y": True, "N": False})
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
    }

    for column in date_columns.get(filename, []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="raise")

            if column != "created_at":
                df[column] = df[column].dt.date

    # Convert missing values to None.
    df = df.astype(object).where(pd.notna(df), None)

    return df


def load_csv_to_table(session, filename, model, table_name):
    df = read_csv(filename)
    records = df.to_dict(orient="records")

    print(f"{table_name}: Reading {len(records)} rows", flush=True)

    for record in records:
        session.merge(model(**record))

    session.flush()

    print(f"{table_name}: Loaded {len(records)} rows", flush=True)


TABLES = [
    ("departments.csv", Department, "departments"),
    ("roles.csv", Role, "roles"),
    ("employees.csv", Employee, "employees"),
    ("employee_assignments.csv", EmployeeAssignment, "employee_assignments"),
    ("salary_components.csv", SalaryComponent, "salary_components"),
    ("salary_revisions.csv", SalaryRevision, "salary_revisions"),
    ("salary_structures.csv", SalaryStructure, "salary_structures"),
]


def load_company_data():
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
                "\nAll company and salary data loaded successfully!",
                flush=True,
            )

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    load_company_data()