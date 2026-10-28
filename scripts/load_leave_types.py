import pandas as pd

from app.database import SessionLocal
from app.models import LeaveType

CSV_PATH = "../03_Data/csv/leave_types.csv"


def load_leave_types():
    df = pd.read_csv(CSV_PATH)

    for column in ["prorated_for_joiners", "carry_forward_allowed"]:
        df[column] = df[column].map({
            "Y": True,
            "N": False,
            "y": True,
            "n": False,
        })

    df = df.astype(object).where(pd.notna(df), None)

    with SessionLocal() as session:
        try:
            for record in df.to_dict(orient="records"):
                session.merge(LeaveType(**record))

            session.commit()
            print(f"Successfully loaded {len(df)} leave types.")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    load_leave_types()