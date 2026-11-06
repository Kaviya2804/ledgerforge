import csv
from pathlib import Path
from decimal import Decimal


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYROLL_FILE = PROJECT_ROOT / "payroll_all_runs.csv"


def get_payslip(employee_id, run_id):
    if not PAYROLL_FILE.exists():
        raise FileNotFoundError("Payroll output file not found")

    with PAYROLL_FILE.open("r", newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)

        for row in rows:
            if (
                row["employee_id"] == employee_id
                and row["run_id"] == run_id
            ):
                gross = Decimal(row["gross_pay"])
                deductions = Decimal(row["total_deductions"])
                net = Decimal(row["net_pay"])

                return {
                    "employee_id": employee_id,
                    "run_id": run_id,
                    "earnings": gross,
                    "gross_pay": gross,
                    "total_deductions": deductions,
                    "net_pay": net,
                }

    return None


def format_indian_currency(amount):
    amount = Decimal(str(amount))
    number = f"{amount:.2f}"
    integer, decimal = number.split(".")

    if len(integer) > 3:
        last_three = integer[-3:]
        remaining = integer[:-3]
        groups = []

        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        integer = ",".join(groups) + "," + last_three

    return f"₹{integer}.{decimal}"
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_payslip_pdf(data, employee_name):
    folder = PROJECT_ROOT / "payslips"
    folder.mkdir(exist_ok=True)

    file_path = folder / f"{data['employee_id']}_{data['run_id']}.pdf"

    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(str(file_path), pagesize=A4)

    content = [
        Paragraph("ZENITH NOVA TECHNOLOGIES", styles["Title"]),
        Paragraph("EMPLOYEE PAYSLIP", styles["Heading2"]),
        Spacer(1, 20),
        Paragraph(f"Employee: {employee_name}", styles["Normal"]),
        Paragraph(f"Employee ID: {data['employee_id']}", styles["Normal"]),
        Paragraph(f"Payroll Run: {data['run_id']}", styles["Normal"]),
        Spacer(1, 20),
    ]

    table = Table([
        ["Description", "Amount"],
        ["Gross Pay / Earnings", format_indian_currency(data["gross_pay"])],
        ["Total Deductions", format_indian_currency(data["total_deductions"])],
        ["NET PAY", format_indian_currency(data["net_pay"])],
    ])

    table.setStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 3), (-1, 3), 14),
        ("PADDING", (0, 0), (-1, -1), 10),
    ])

    content.append(table)
    document.build(content)

    return file_path