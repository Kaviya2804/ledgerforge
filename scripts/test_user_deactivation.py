import sys
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.models import User
from app.auth_service import create_access_token
from app.security import get_current_user

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# 1. Create a separate test database copy
test_db_path = Path("task13_deactivation_test.db")

source_engine = create_engine(settings.database_url)
source_connection = source_engine.raw_connection()

try:
    destination = sqlite3.connect(test_db_path)
    source_connection.driver_connection.backup(destination)
    destination.close()
finally:
    source_connection.close()
    source_engine.dispose()


# 2. Connect to the test database
test_engine = create_engine(f"sqlite:///{test_db_path}")

TestSession = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

db = TestSession()

try:
    # 3. Find the demo employee
    user = db.query(User).filter(User.user_id == "U-0002").first()

    if user is None:
        raise Exception("Test employee U-0002 not found")

    if not user.is_active:
        raise Exception("Test employee is already inactive")

    # 4. Generate a valid token before deactivation
    token = create_access_token(user.user_id)

    print("Token generated: SUCCESS")
    print("User active before deactivation:", user.is_active)

    # 5. Deactivate the user in the test database
    user.is_active = False
    db.commit()

    print("User active after deactivation:", user.is_active)

    # 6. Try using the existing token
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db,
        )

        print("TEST FAILED: Inactive user was allowed")

    except HTTPException as error:
        if error.status_code == 401:
            print("TEST PASSED: Existing token rejected")
            print("Response status: 401 Unauthorized")
        else:
            raise

finally:
    db.close()
    test_engine.dispose()