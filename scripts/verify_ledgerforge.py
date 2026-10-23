from app.database import SessionLocal
from sqlalchemy import text

tables = [
    "departments",
    "roles",
    "employees",
    "employee_assignments",
    "salary_components",
    "salary_revisions",
    "salary_structures",
]

with SessionLocal() as session:
    for table in tables:
        query = text(f"SELECT COUNT(*) FROM {table}")
        count = session.execute(query).scalar()
        print(f"{table}: {count} rows")