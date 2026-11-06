import pandas as pd
from pathlib import Path
from datetime import date
from decimal import Decimal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT.parent / "03_Data" / "csv"

accounts = pd.read_csv(DATA_DIR / "chart_of_accounts.csv")

journal_entries = []
journal_lines = []


def create_journal_entry(entry_id, entry_date, description, lines):
    total_debit = sum(Decimal(str(x["debit"])) for x in lines)
    total_credit = sum(Decimal(str(x["credit"])) for x in lines)

    if total_debit != total_credit:
        raise ValueError("Journal entry is unbalanced: debit must equal credit")

    if any(x["debit"] < 0 or x["credit"] < 0 for x in lines):
        raise ValueError("Debit and credit cannot be negative")

    journal_entries.append({
        "entry_id": entry_id,
        "entry_date": str(entry_date),
        "description": description,
        "status": "POSTED",
        "total_debit": float(total_debit),
        "total_credit": float(total_credit)
    })

    for i, line in enumerate(lines, start=1):
        journal_lines.append({
            "entry_id": entry_id,
            "line_no": i,
            **line
        })

    return journal_entries[-1]


def account_balance(account_code, as_of_date):
    account = accounts[
        accounts["account_code"].astype(str) == str(account_code)
    ]

    if account.empty:
        raise ValueError("Account not found")

    normal_balance = account.iloc[0]["normal_balance"]
    balance = Decimal("0")

    for entry in journal_entries:
        if entry["status"] != "POSTED":
            continue

        if entry["entry_date"] > str(as_of_date):
            continue

        for line in journal_lines:
            if (
                line["entry_id"] == entry["entry_id"]
                and str(line["account_code"]) == str(account_code)
            ):
                debit = Decimal(str(line["debit"]))
                credit = Decimal(str(line["credit"]))

                if normal_balance == "DEBIT":
                    balance += debit - credit
                else:
                    balance += credit - debit

    return balance


def reverse_journal_entry(entry_id, reversal_id, reversal_date):
    original = next((e for e in journal_entries if e["entry_id"] == entry_id), None)

    if not original or original["status"] != "POSTED":
        raise ValueError("Posted journal entry not found")

    original_lines = [l for l in journal_lines if l["entry_id"] == entry_id]

    reversed_lines = [
        {
            "account_code": l["account_code"],
            "debit": l["credit"],
            "credit": l["debit"]
        }
        for l in original_lines
    ]

    return create_journal_entry(
        reversal_id,
        reversal_date,
        f"Reversal of {entry_id}",
        reversed_lines
    )
def export_journal_entries(output_dir):
    from pathlib import Path
    import pandas as pd

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(journal_entries).to_csv(
        output_dir / "journal_entries.csv", index=False
    )

    pd.DataFrame(journal_lines).to_csv(
        output_dir / "journal_lines.csv", index=False
    )
def edit_journal_entry(entry_id, updated_data):
    entry = next(
        (e for e in journal_entries if e["entry_id"] == entry_id),
        None
    )

    if not entry:
        raise ValueError("Journal entry not found")

    if entry["status"] == "POSTED":
        raise ValueError(
            "Posted journal entries cannot be edited. Create a reversal entry instead."
        )

    entry.update(updated_data)
    return entry