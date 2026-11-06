import csv
from pathlib import Path
from decimal import Decimal
from datetime import date

from app.config import settings
from app.database import SessionLocal
from app.models import TaxSlab, TaxParameter, StatutoryRate

DATA_DIR = Path(settings.data_dir)


def read_csv(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def decimal_value(value):
    return Decimal(value.strip()) if value and value.strip() else None


def date_value(value):
    return date.fromisoformat(value.strip()) if value and value.strip() else None


slabs = []
for row in read_csv("tax_slabs.csv"):
    slabs.append(TaxSlab(
        slab_id=row["slab_id"],
        regime=row["regime"],
        financial_year=row["financial_year"],
        income_from=decimal_value(row["income_from"]),
        income_to=decimal_value(row.get("income_to")),
        rate_percent=decimal_value(row["rate_percent"]),
        effective_from=date_value(row["effective_from"]),
        note=row.get("note") or None
    ))

parameters = []
for row in read_csv("tax_parameters.csv"):
    parameters.append(TaxParameter(
        parameter=row["parameter"],
        value=decimal_value(row["value"]),
        note=row.get("note") or None
    ))

rates = []
for row in read_csv("statutory_rates.csv"):
    rates.append(StatutoryRate(
        parameter=row["parameter"],
        value=decimal_value(row["value"]),
        unit=row.get("unit") or None,
        note=row.get("note") or None,
        effective_from=date_value(row["effective_from"])
    ))

with SessionLocal() as db:
    with db.begin():
        db.query(TaxSlab).delete()
        db.query(TaxParameter).delete()
        db.query(StatutoryRate).delete()

        db.add_all(slabs)
        db.add_all(parameters)
        db.add_all(rates)

print("Task 14 rules loaded successfully!")
print("Tax slabs:", len(slabs))
print("Tax parameters:", len(parameters))
print("Statutory rates:", len(rates))
