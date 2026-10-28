from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.attendance_service import monthly_summary
from app.models import Attendance, Holiday


def test_monthly_summary_excludes_weekends_and_holidays():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    try:
        with TestSession() as session:
            session.add(
                Holiday(
                    holiday_date=date(2025, 4, 14),
                    holiday_name="Test Holiday",
                    holiday_type="Public",
                    weekday="Mon",
                    falls_on_weekend=False,
                    calendar_note=None,
                )
            )

            session.add_all([
                Attendance(
                    attendance_id="TEST-ATT-001",
                    employee_id="TEST-EMP-001",
                    attendance_date=date(2025, 4, 1),
                    weekday="Tue",
                    status="PRESENT",
                    late_flag="N",
                    overtime_hours=Decimal("1.50"),
                ),
                Attendance(
                    attendance_id="TEST-ATT-002",
                    employee_id="TEST-EMP-001",
                    attendance_date=date(2025, 4, 5),
                    weekday="Sat",
                    status="PRESENT",
                    late_flag="Y",
                    overtime_hours=Decimal("2.00"),
                ),
                Attendance(
                    attendance_id="TEST-ATT-003",
                    employee_id="TEST-EMP-001",
                    attendance_date=date(2025, 4, 14),
                    weekday="Mon",
                    status="WFH",
                    late_flag="Y",
                    overtime_hours=Decimal("3.00"),
                ),
            ])

            session.commit()

            result = monthly_summary(
                session,
                "TEST-EMP-001",
                "2025-04",
            )

            assert result["present_days"] == 1
            assert result["wfh_days"] == 0
            assert result["absent_days"] == 0
            assert result["late_days"] == 0
            assert result["overtime_hours"] == Decimal("1.50")

    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()