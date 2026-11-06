import pandas as pd
from pathlib import Path
from decimal import Decimal
from datetime import date


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT.parent / "03_Data" / "csv"

AR_ACCOUNT = "1100"
GST_ACCOUNT = "2200"


def load_invoice_data():
    invoices = pd.read_csv(DATA_DIR / "invoices.csv")
    items = pd.read_csv(DATA_DIR / "invoice_items.csv")
    journal_entries = pd.read_csv(DATA_DIR / "journal_entries.csv")

    return invoices, items, journal_entries


def get_existing_invoice_ids(journal_entries):
    existing = journal_entries[
        (journal_entries["source_type"] == "INVOICE")
        & (journal_entries["status"] == "POSTED")
    ]

    return set(existing["source_id"].astype(str))


def create_invoice_lines(invoice, invoice_items):
    invoice_id = str(invoice["invoice_id"])

    items = invoice_items[
        invoice_items["invoice_id"].astype(str) == invoice_id
    ]

    if items.empty:
        raise ValueError(f"No invoice items found for {invoice_id}")

    lines = []

    # Debit Accounts Receivable
    lines.append({
        "account_code": AR_ACCOUNT,
        "debit": Decimal(str(invoice["total_amount"])),
        "credit": Decimal("0")
    })

    # Credit revenue accounts based on invoice items
    revenue_totals = items.groupby("revenue_account")["amount"].sum()

    for account_code, amount in revenue_totals.items():
        lines.append({
            "account_code": str(account_code),
            "debit": Decimal("0"),
            "credit": Decimal(str(amount))
        })

    # Credit GST Output Payable
    gst_amount = Decimal(str(invoice["gst_amount"]))

    if gst_amount > 0:
        lines.append({
            "account_code": GST_ACCOUNT,
            "debit": Decimal("0"),
            "credit": gst_amount
        })

    return lines


def prepare_invoice_postings():
    invoices, items, journal_entries = load_invoice_data()

    existing_ids = get_existing_invoice_ids(journal_entries)

    postings = []
    skipped = []

    for _, invoice in invoices.iterrows():
        invoice_id = str(invoice["invoice_id"])
        status = str(invoice["status"]).upper()

        # Draft and cancelled invoices must never be posted
        if status in ["DRAFT", "CANCELLED"]:
            skipped.append((invoice_id, status))
            continue

        # Do not post invoices already linked to an existing journal
        if pd.notna(invoice["ledger_entry_id"]) or invoice_id in existing_ids:
            skipped.append((invoice_id, "ALREADY_POSTED_OR_LINKED"))
            continue

        # Carried-forward invoices are covered by opening balances
        if str(invoice["carried_in_from_prior_period"]).upper() == "Y":
            skipped.append((invoice_id, "CARRIED_FORWARD"))
            continue

        lines = create_invoice_lines(invoice, items)

        postings.append({
            "invoice_id": invoice_id,
            "invoice_number": invoice["invoice_number"],
            "entry_date": str(invoice["invoice_date"]),
            "description": f"Invoice {invoice['invoice_number']}",
            "lines": lines
        })

    return postings, skipped