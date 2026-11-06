from pathlib import Path
import secrets

import pandas as pd
from sqlalchemy import select

from app.config import settings
from app.database import engine
from app.models import User
from app.auth_service import hash_password


DATA_DIR = Path(settings.data_dir)
CSV_PATH = DATA_DIR / "users.csv"


def load_users():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Users CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    required_columns = {
        "user_id",
        "employee_id",
        "username",
        "role",
        "is_active",
        "mfa_enabled",
        "last_login_at",
        "created_at",
    }

    if set(df.columns) != required_columns | {"password_policy_note"}:
        raise ValueError("Users CSV columns do not match the expected columns.")

    records = []

    for row in df.to_dict(orient="records"):
        # Generate a unique random password.
        # Only its bcrypt hash will be stored.
        temporary_password = secrets.token_urlsafe(32)

        records.append({
            "user_id": row["user_id"],
            "employee_id": row["employee_id"],
            "username": row["username"],
            "password_hash": hash_password(temporary_password),
            "role": row["role"].upper(),
            "is_active": str(row["is_active"]).upper() == "Y",
            "mfa_enabled": str(row["mfa_enabled"]).upper() == "Y",
            "last_login_at": (
                pd.to_datetime(row["last_login_at"]).to_pydatetime()
                if pd.notna(row["last_login_at"])
                else None
            ),
            "created_at": (
                pd.to_datetime(row["created_at"]).to_pydatetime()
                if pd.notna(row["created_at"])
                else None
            ),
        })

    # Insert users without deleting existing user records.
    with engine.begin() as connection:
        existing_ids = set(
            connection.execute(
                select(User.user_id)
            ).scalars().all()
        )

        new_records = [
            record for record in records
            if record["user_id"] not in existing_ids
        ]

        if new_records:
            connection.execute(
                User.__table__.insert(),
                new_records,
            )

    print("User loading completed.")
    print(f"CSV users: {len(records)}")
    print(f"New users inserted: {len(new_records)}")
    print(f"Existing users skipped: {len(records) - len(new_records)}")
    print("Passwords stored only as bcrypt hashes.")


if __name__ == "__main__":
    load_users()