import pandas as pd
from pathlib import Path
from datetime import date
from decimal import Decimal

from .config import settings


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = (PROJECT_ROOT / settings.data_dir).resolve()


def money(value):
    if pd.isna(value) or value is None or value == "":
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


def load_financial_data():
    entries = pd.read_csv(
        DATA_DIR / "journal_entries.csv",
        dtype={"entry_id": str, "status": str},
    )

    lines = pd.read_csv(
        DATA_DIR / "journal_lines.csv",
        dtype={
            "entry_id": str,
            "account_code": str,
            "debit": str,
            "credit": str,
        },
    )

    accounts = pd.read_csv(
        DATA_DIR / "chart_of_accounts.csv",
        dtype={"account_code": str},
    )

    entries = entries[entries["status"] == "POSTED"].copy()

    lines = lines.merge(
        entries[["entry_id", "entry_date"]],
        on="entry_id",
        how="inner",
    )

    accounts = accounts[
        (accounts["is_group"] == "N")
        & (accounts["is_active"] == "Y")
    ].copy()

    lines = lines.merge(
        accounts,
        on="account_code",
        how="inner",
    )

    return lines, accounts


def get_trial_balance(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")

    lines, accounts = load_financial_data()

    lines = lines[
        (lines["entry_date"] >= start_date.isoformat())
        & (lines["entry_date"] <= end_date.isoformat())
    ]

    totals = {}

    for _, row in lines.iterrows():
        code = row["account_code"]

        if code not in totals:
            totals[code] = {
                "debit": Decimal("0.00"),
                "credit": Decimal("0.00"),
            }

        totals[code]["debit"] += money(row["debit"])
        totals[code]["credit"] += money(row["credit"])

    result = []

    for _, account in accounts.iterrows():
        code = account["account_code"]
        values = totals.get(code, {
            "debit": Decimal("0.00"),
            "credit": Decimal("0.00"),
        })

        net = values["debit"] - values["credit"]

        if account["normal_balance"] == "DEBIT":
            balance_debit = max(net, Decimal("0.00"))
            balance_credit = max(-net, Decimal("0.00"))
        else:
            balance_credit = max(-net, Decimal("0.00"))
            balance_debit = max(net, Decimal("0.00"))

        result.append({
            "account_code": code,
            "account_name": account["account_name"],
            "debit": str(values["debit"]),
            "credit": str(values["credit"]),
            "balance_debit": str(balance_debit),
            "balance_credit": str(balance_credit),
        })

    return {
        "report": "Trial Balance",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "accounts": result,
        "total_debit": str(sum(
            (money(x["debit"]) for x in result),
            Decimal("0.00"),
        )),
        "total_credit": str(sum(
            (money(x["credit"]) for x in result),
            Decimal("0.00"),
        )),
    }


def get_profit_loss(start_date: date, end_date: date):
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")

    lines, _ = load_financial_data()

    lines = lines[
        (lines["entry_date"] >= start_date.isoformat())
        & (lines["entry_date"] <= end_date.isoformat())
    ]

    revenue = Decimal("0.00")
    expenses = Decimal("0.00")
    details = []

    grouped = lines.groupby(
        ["account_code", "account_name", "account_type"]
    )

    for (code, name, account_type), group in grouped:
        debit = sum(
            (money(x) for x in group["debit"]),
            Decimal("0.00"),
        )
        credit = sum(
            (money(x) for x in group["credit"]),
            Decimal("0.00"),
        )

        if account_type == "INCOME":
            amount = credit - debit
            revenue += amount
        elif account_type == "EXPENSE":
            amount = debit - credit
            expenses += amount
        else:
            continue

        details.append({
            "account_code": code,
            "account_name": name,
            "account_type": account_type,
            "amount": str(amount),
        })

    return {
        "report": "Profit and Loss",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "revenue": str(revenue),
        "expenses": str(expenses),
        "net_profit": str(revenue - expenses),
        "accounts": details,
    }


def get_balance_sheet(as_of_date: date):
    lines, accounts = load_financial_data()

    lines = lines[
        lines["entry_date"] <= as_of_date.isoformat()
    ]

    balances = {}

    for _, row in lines.iterrows():
        code = row["account_code"]

        if code not in balances:
            balances[code] = Decimal("0.00")

        debit = money(row["debit"])
        credit = money(row["credit"])

        if row["account_type"] == "ASSET":
            balances[code] += debit - credit
        else:
            balances[code] += credit - debit

    assets = Decimal("0.00")
    liabilities = Decimal("0.00")
    equity = Decimal("0.00")
    details = []

    for _, account in accounts.iterrows():
        code = account["account_code"]
        account_type = account["account_type"]
        amount = balances.get(code, Decimal("0.00"))

        if account_type == "ASSET":
            assets += amount
        elif account_type == "LIABILITY":
            liabilities += amount
        elif account_type == "EQUITY":
            equity += amount
        else:
            continue

        details.append({
            "account_code": code,
            "account_name": account["account_name"],
            "account_type": account_type,
            "balance": str(amount),
        })

    income = Decimal("0.00")
    expenses = Decimal("0.00")

    for _, row in lines.iterrows():
        if row["account_type"] == "INCOME":
            income += money(row["credit"]) - money(row["debit"])
        elif row["account_type"] == "EXPENSE":
            expenses += money(row["debit"]) - money(row["credit"])

    current_profit = income - expenses
    total_liabilities_equity = (
        liabilities + equity + current_profit
    )

    return {
        "report": "Balance Sheet",
        "as_of_date": as_of_date.isoformat(),
        "assets": str(assets),
        "liabilities": str(liabilities),
        "equity": str(equity),
        "current_profit": str(current_profit),
        "total_liabilities_equity_profit": str(
            total_liabilities_equity
        ),
        "difference": str(assets - total_liabilities_equity),
        "is_balanced": assets == total_liabilities_equity,
        "accounts": details,
    }