"""make payroll pay date nullable

Revision ID: 083a50d6d2c2
Revises: f003a4b1188f
Create Date: 2026-11-03 17:56:32.858706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '083a50d6d2c2'
down_revision: Union[str, Sequence[str], None] = 'f003a4b1188f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payroll_runs") as batch_op:
        batch_op.alter_column(
            "pay_date",
            existing_type=sa.DATE(),
            nullable=True,
        )


def downgrade() -> None:
    op.alter_column(
        'payroll_runs',
        'pay_date',
        existing_type=sa.DATE(),
        nullable=False
    )