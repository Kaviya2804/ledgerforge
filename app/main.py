from fastapi import FastAPI, APIRouter

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



app = FastAPI(
    title="LedgerForge API",
    version="1.0.0-rc1",
    description=(
        "Payroll, accounting and employee data engine "
        "for Zenith Nova Technologies"
    ),
)

api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(auth.router)
api_v1.include_router(departments.router)
api_v1.include_router(employees.router)
api_v1.include_router(salary.router)
api_v1.include_router(payslips.router)
api_v1.include_router(tax_rules.router)
api_v1.include_router(statutory_reports.router)
api_v1.include_router(financial_reports.router)
api_v1.include_router(payroll_jobs.router)


@api_v1.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "ledgerforge",
    }


app.include_router(api_v1)
