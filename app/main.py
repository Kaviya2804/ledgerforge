import logging
import json

from fastapi import FastAPI, APIRouter, HTTPException
from sqlalchemy import text

from .database import Base, engine
from .routers import (
    departments,
    employees,
    salary,
    payslips,
    auth,
    tax_rules,
    statutory_reports,
    financial_reports,
    payroll_jobs,
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        })


logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","message":"%(message)s"}',
    force=True,
)


app = FastAPI(
    title="LedgerForge API",
    version="1.0.0-rc1",
    description=(
        "Payroll, accounting and employee data engine "
        "for Zenith Nova Technologies"
    ),
)

api_v1 = APIRouter(prefix="/api/v1")


# Register all routers
api_v1.include_router(auth.router)
api_v1.include_router(departments.router)
api_v1.include_router(employees.router)
api_v1.include_router(salary.router)
api_v1.include_router(payslips.router)
api_v1.include_router(tax_rules.router)
api_v1.include_router(statutory_reports.router)
api_v1.include_router(financial_reports.router)
api_v1.include_router(payroll_jobs.router)


# Improved health check with database verification
@api_v1.get("/health", tags=["system"])
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "ledgerforge",
            "database": "connected",
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "service": "ledgerforge",
                "database": "disconnected",
            },
        )


# Register API routes
app.include_router(api_v1)