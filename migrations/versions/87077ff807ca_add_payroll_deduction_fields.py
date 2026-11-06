"""add payroll deduction fields

Revision ID: 87077ff807ca
Revises: e61f5de791f3
Create Date: 2026-11-04 13:07:48.620425
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "87077ff807ca"
down_revision: Union[str, Sequence[str], None] = "e61f5de791f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payroll_items",
        sa.Column(
            "pf_employee",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "payroll_items",
        sa.Column(
            "esi_employee",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "payroll_items",
        sa.Column(
            "professional_tax",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "payroll_items",
        sa.Column(
            "tds",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "payroll_items",
        sa.Column(
            "other_deductions",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "payroll_items",
        sa.Column(
            "net_pay",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("payroll_items", "net_pay")
    op.drop_column("payroll_items", "other_deductions")
    op.drop_column("payroll_items", "tds")
    op.drop_column("payroll_items", "professional_tax")
    op.drop_column("payroll_items", "esi_employee")
    op.drop_column("payroll_items", "pf_employee")