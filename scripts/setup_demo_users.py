from sqlalchemy import select

from app.config import settings
from app.database import engine
from app.models import User
from app.auth_service import hash_password


DEMO_USERS = [
    {
        "user_id": "U-0099",
        "password": settings.demo_admin_password,
    },
    {
        "user_id": "U-0011",
        "password": settings.demo_hr_password,
    },
    {
        "user_id": "U-0002",
        "password": settings.demo_employee_password,
    },
]


def setup_demo_users():
    with engine.begin() as connection:
        for demo in DEMO_USERS:
            user = connection.execute(
                select(User.__table__).where(
                    User.user_id == demo["user_id"]
                )
            ).mappings().first()

            if user is None or not user["is_active"]:
                raise ValueError(
                    f"Demo user missing or inactive: {demo['user_id']}"
                )

            connection.execute(
                User.__table__.update()
                .where(User.user_id == demo["user_id"])
                .values(password_hash=hash_password(demo["password"]))
            )

    print("Demo accounts updated successfully.")
    print("ADMIN, HR and EMPLOYEE password hashes saved.")
    print("Plaintext passwords were not stored.")


if __name__ == "__main__":
    setup_demo_users()