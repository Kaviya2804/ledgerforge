import pandas as pd
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT.parent / "03_Data" / "csv"


def get_receivables(as_of_date=None):
    if as_of_date is None:
        as_of_date = date.today()

    invoices = pd.read_csv(DATA_DIR / "invoices.csv")
    clients = pd.read_csv(DATA_DIR / "clients.csv")

    # Exclude invoices that should not be included in receivables
    invoices = invoices[
        ~invoices["status"].isin(["DRAFT", "CANCELLED"])
    ].copy()

    # Only invoices with an outstanding balance
    invoices = invoices[invoices["balance_due"] > 0].copy()

    invoices["due_date"] = pd.to_datetime(
        invoices["due_date"], errors="coerce"
    )

    invoices["receivable_status"] = invoices["due_date"].apply(
        lambda d: "OVERDUE"
        if pd.notna(d) and d.date() < as_of_date
        else "OPEN"
    )

    report = invoices.merge(
        clients[["client_id", "client_name"]],
        on="client_id",
        how="left"
    )

    columns = [
        "invoice_id",
        "invoice_number",
        "client_id",
        "client_name",
        "invoice_date",
        "due_date",
        "total_amount",
        "amount_paid",
        "balance_due",
        "receivable_status"
    ]

    return report[columns].sort_values(
        by=["receivable_status", "due_date"]
    ).reset_index(drop=True)


def receivables_summary(as_of_date=None):
    report = get_receivables(as_of_date)

    return {
        "open_invoice_count": len(report),
        "total_receivables": round(
            float(report["balance_due"].sum()), 2
        ),
        "overdue_count": int(
            (report["receivable_status"] == "OVERDUE").sum()
        ),
        "overdue_amount": round(
            float(
                report.loc[
                    report["receivable_status"] == "OVERDUE",
                    "balance_due"
                ].sum()
            ), 2
        )
    }