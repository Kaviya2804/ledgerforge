from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.payslip_service import get_payslip, create_payslip_pdf
from app.security import get_current_user


router = APIRouter(prefix="/payslips", tags=["payslips"])


@router.get("/{employee_id}/{run_id}")
def download_payslip(
    employee_id: str,
    run_id: str,
    current_user=Depends(get_current_user),
):
    # Employees can access only their own payslips
    if current_user.role == "EMPLOYEE":
        if current_user.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can access only their own payslips",
            )

    # Only ADMIN, HR and EMPLOYEE roles are permitted
    elif current_user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    data = get_payslip(employee_id, run_id)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found",
        )

    pdf_path = create_payslip_pdf(data, employee_id)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{employee_id}_{run_id}.pdf",
    )