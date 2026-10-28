# LedgerForge - FastAPI Project

## Run this project in 10 steps

1. Install Python 3.11 or newer.
2. Install Git and Visual Studio Code.
3. Clone or download the project.
4. Open the project folder in VS Code.
5. Create a virtual environment using `python -m venv .venv`.
6. Activate it using `.venv\Scripts\activate` on Windows.
7. Install dependencies using `pip install -r requirements.txt`.
8. Copy `.env.example` to `.env` and configure the settings if required.
9. Run `python -m scripts.seed_example`.
10. Start the API using `uvicorn app.main:app --reload`.

## Test the API

Open http://127.0.0.1:8000/docs

Try the `GET /departments` endpoint.

## Run tests

```bash
python -m pytest
Attendance Management Policy

Missing Check-out Policy

- If an employee has a check-in time but no check-out time, the attendance record will be flagged for review.
- Working hours and overtime will not be calculated for records with a missing check-out time.
- The record will remain pending until the missing check-out time is verified by the manager.
- Weekends and company holidays are excluded from monthly attendance summaries.
- Attendance records marked as "PRESENT" and "WFH" are counted separately.
- Late attendance is counted only on eligible working days.
### Missing Checkout Rule

If an employee has a check-in time but no check-out time,
the attendance record will be treated as incomplete.

Overtime hours will not be calculated for incomplete records.
The missing checkout must be verified and corrected before
the attendance summary is finalized.